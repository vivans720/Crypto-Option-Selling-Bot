import asyncio
import websockets
import json
import logging
from typing import Dict, Callable, List

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DeribitWebsocketClient:
    def __init__(self, testnet: bool = False):
        self.url = "wss://test.deribit.com/ws/api/v2" if testnet else "wss://www.deribit.com/ws/api/v2"
        self.websocket = None
        self.subscriptions: List[str] = []
        self.callbacks: Dict[str, List[Callable]] = {}
        self.running = False

    async def connect(self):
        logger.info(f"Connecting to Deribit WS: {self.url}")
        self.websocket = await websockets.connect(self.url)
        self.running = True
        logger.info("Connected.")

    async def subscribe(self, channels: List[str], callback: Callable):
        self.subscriptions.extend(channels)
        for channel in channels:
            if channel not in self.callbacks:
                self.callbacks[channel] = []
            self.callbacks[channel].append(callback)
        
        msg = {
            "jsonrpc": "2.0",
            "method": "public/subscribe",
            "id": 42,
            "params": {"channels": channels}
        }
        await self.websocket.send(json.dumps(msg))
        logger.info(f"Subscribed to: {channels}")

    async def listen(self):
        while self.running:
            try:
                if not self.websocket or not self.websocket.open:
                    await self.connect()
                    if self.subscriptions:
                        await self.subscribe(self.subscriptions, None) # Resubscribe logic

                async for response in self.websocket:
                    data = json.loads(response)
                    if "params" in data and "channel" in data["params"]:
                        channel = data["params"]["channel"]
                        if channel in self.callbacks:
                            for cb in self.callbacks[channel]:
                                await cb(data["params"]["data"])
                    elif "error" in data:
                        logger.error(f"WS Error: {data['error']}")
            except Exception as e:
                logger.warning(f"WS Error: {e}. Reconnecting in 5s...")
                await asyncio.sleep(5)

    async def stop(self):
        self.running = False
        if self.websocket:
            await self.websocket.close()
