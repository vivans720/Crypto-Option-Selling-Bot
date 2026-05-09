import asyncio
import websockets
import json
import logging
import time
from typing import Dict, Callable, List, Optional
import hmac
import hashlib

logger = logging.getLogger(__name__)

class DeribitWebsocketClient:
    def __init__(self, client_id: str = None, client_secret: str = None, testnet: bool = False):
        self.url = "wss://test.deribit.com/ws/api/v2" if testnet else "wss://www.deribit.com/ws/api/v2"
        self.client_id = client_id
        self.client_secret = client_secret
        self.websocket = None
        self.subscriptions: List[str] = []
        self.callbacks: Dict[str, List[Callable]] = {}
        self.running = False
        self.is_auth = False
        self._reconnect_delay = 1

    async def connect(self):
        while True:
            try:
                logger.info(f"Connecting to {self.url}...")
                self.websocket = await websockets.connect(
                    self.url,
                    ping_interval=20,
                    ping_timeout=10
                )
                self.running = True
                self._reconnect_delay = 1
                logger.info("Connected.")
                
                if self.client_id and self.client_secret:
                    await self.authenticate()
                
                if self.subscriptions:
                    await self.subscribe(self.subscriptions, None, resub=True)
                
                return
            except Exception as e:
                logger.error(f"Connection failed: {e}. Retrying in {self._reconnect_delay}s...")
                await asyncio.sleep(self._reconnect_delay)
                self._reconnect_delay = min(self._reconnect_delay * 2, 60)

    async def authenticate(self):
        timestamp = int(time.time() * 1000)
        nonce = "abc"
        data = ""
        signature = hmac.new(
            self.client_secret.encode('utf-8'),
            f"{timestamp}\n{nonce}\n{data}".encode('utf-8'),
            hashlib.sha256
        ).hexdigest()

        msg = {
            "jsonrpc": "2.0",
            "id": 9929,
            "method": "public/auth",
            "params": {
                "grant_type": "client_signature",
                "client_id": self.client_id,
                "timestamp": timestamp,
                "nonce": nonce,
                "data": data,
                "signature": signature
            }
        }
        await self.websocket.send(json.dumps(msg))
        resp = await self.websocket.recv()
        data = json.loads(resp)
        if "result" in data:
            self.is_auth = True
            logger.info("Authenticated.")
            # Start heartbeat for private connection
            asyncio.create_task(self._heartbeat())
        else:
            logger.error(f"Auth failed: {data}")

    async def _heartbeat(self):
        while self.running and self.is_auth:
            try:
                await self.websocket.send(json.dumps({
                    "jsonrpc": "2.0",
                    "id": 8000,
                    "method": "public/test",
                    "params": {}
                }))
                await asyncio.sleep(30)
            except:
                break

    async def subscribe(self, channels: List[str], callback: Optional[Callable], resub=False):
        if not resub:
            self.subscriptions.extend(channels)
            if callback:
                for channel in channels:
                    if channel not in self.callbacks:
                        self.callbacks[channel] = []
                    self.callbacks[channel].append(callback)
        
        msg = {
            "jsonrpc": "2.0",
            "method": "public/subscribe" if not self.is_auth else "private/subscribe",
            "id": 42,
            "params": {"channels": channels}
        }
        if self.websocket and self.websocket.open:
            await self.websocket.send(json.dumps(msg))
            logger.info(f"Subscribed to: {channels}")

    async def listen(self):
        while self.running:
            try:
                if not self.websocket or not self.websocket.open:
                    await self.connect()

                async for response in self.websocket:
                    data = json.loads(response)
                    if "params" in data and "channel" in data["params"]:
                        channel = data["params"]["channel"]
                        if channel in self.callbacks:
                            for cb in self.callbacks[channel]:
                                await cb(data["params"]["data"])
                    elif "error" in data:
                        logger.error(f"WS RPC Error: {data['error']}")
                    elif "id" in data and data["id"] == 8000:
                        pass # Heartbeat response
            except websockets.exceptions.ConnectionClosed:
                logger.warning("WS Connection closed. Reconnecting...")
            except Exception as e:
                logger.error(f"WS Listen Error: {e}")
                await asyncio.sleep(5)

    async def stop(self):
        self.running = False
        if self.websocket:
            await self.websocket.close()
