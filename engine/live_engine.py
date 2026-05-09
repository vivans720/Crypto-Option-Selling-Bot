import asyncio
import logging
from datetime import datetime, timezone
from config.settings import settings
from api.websocket_client import DeribitWebsocketClient
from api.deribit import fetch_option_chain
from api.notifications import TelegramNotifier
from engine.paper_broker import PaperBroker
from strategy.core import select_strikes, calculate_exit
from database.manager import DatabaseManager
from utils.logger import logger, trade_logger

class LiveEngine:
    def __init__(self):
        self.db = DatabaseManager()
        self.broker = PaperBroker() # PaperBroker should use settings internally
        self.ws = DeribitWebsocketClient(
            client_id=settings.DERIBIT_CLIENT_ID,
            client_secret=settings.DERIBIT_CLIENT_SECRET,
            testnet=settings.TESTNET
        )
        self.notifier = TelegramNotifier(settings.TELEGRAM_BOT_TOKEN, settings.TELEGRAM_CHAT_ID)
        
        self.active_trade = None
        self.prices = {}
        self.running = False

    async def startup(self):
        logger.info("Initializing Live Engine...")
        # Recover state
        open_trades = self.db.get_open_trades()
        if open_trades:
            self.active_trade = open_trades[0]
            logger.info(f"Recovered active trade: {self.active_trade.id}")
            # Resubscribe
            channels = [
                f"ticker.{self.active_trade.call_instrument}.raw",
                f"ticker.{self.active_trade.put_instrument}.raw"
            ]
            await self.ws.subscribe(channels, self._on_ticker)
        
        await self.ws.connect()
        asyncio.create_task(self.ws.listen())
        self.running = True
        await self.notifier.send_message("<b>[SYSTEM START]</b> Bot initialized.")

    async def _on_ticker(self, data):
        instrument = data['instrument_name']
        self.prices[instrument] = data['mark_price']
        if self.active_trade:
            await self.check_exits()

    async def check_exits(self):
        if not self.active_trade or self.active_trade.status != "OPEN":
            return

        c_mark = self.prices.get(self.active_trade.call_instrument)
        p_mark = self.prices.get(self.active_trade.put_instrument)

        if c_mark is not None and p_mark is not None:
            pos_state = {
                'call_entry_price': self.active_trade.entry_price_call,
                'put_entry_price': self.active_trade.entry_price_put
            }
            current_prices = {
                'call_mark': c_mark,
                'put_mark': p_mark
            }
            
            exit_reason = calculate_exit(pos_state, current_prices, settings.SL_MULTIPLIER)
            if exit_reason:
                await self.force_exit(exit_reason, c_mark, p_mark)

    async def run_loop(self):
        while self.running:
            try:
                now = datetime.now(timezone.utc)
                current_time = now.strftime("%H:%M")
                
                # Entry Logic
                if settings.ENTRY_WINDOW_START <= current_time <= settings.ENTRY_WINDOW_END:
                    if not self.active_trade:
                        await self.attempt_entry(now)
                
                # Expiry Logic
                if current_time >= "23:55" and self.active_trade:
                    # Fetch latest marks before closing
                    c_mark = self.prices.get(self.active_trade.call_instrument, 0)
                    p_mark = self.prices.get(self.active_trade.put_instrument, 0)
                    await self.force_exit("EXPIRY", c_mark, p_mark)

                # Heartbeat
                if now.minute % 5 == 0 and now.second < 10:
                    logger.debug("Heartbeat check.")

                await asyncio.sleep(10)
            except Exception as e:
                logger.error(f"Loop Error: {e}", exc_info=True)
                await asyncio.sleep(30)

    async def attempt_entry(self, now: datetime):
        # Risk Checks
        daily_pnl = self.db.get_total_pnl() # Simplified: should be today's only
        if daily_pnl < -settings.MAX_DAILY_LOSS:
            logger.warning("Max daily loss reached. Skipping entry.")
            return

        logger.info("Attempting entry...")
        try:
            chain = fetch_option_chain(settings.TRADING_SYMBOL)
            strikes = select_strikes(chain, settings.TARGET_DELTA_MIN, settings.TARGET_DELTA_MAX)
            
            if strikes['call'] and strikes['put']:
                # Filter for liquidity
                if strikes['call']['bid_price'] < 0.0001 or strikes['put']['bid_price'] < 0.0001:
                    logger.warning("Low liquidity, skipping.")
                    return

                self.active_trade = await self.broker.execute_entry(strikes['call'], strikes['put'], now)
                
                # DB Save
                self.db.save_trade(vars(self.active_trade)) # Simplified mapping
                
                await self.notifier.notify_entry(
                    self.active_trade.id, 
                    strikes['call'].get('spot_price', 0),
                    strikes['call']['strike'], 
                    strikes['put']['strike'], 
                    strikes['call']['mark_price'] + strikes['put']['mark_price']
                )
                
                channels = [
                    f"ticker.{strikes['call']['instrument_name']}.raw",
                    f"ticker.{strikes['put']['instrument_name']}.raw"
                ]
                await self.ws.subscribe(channels, self._on_ticker)
            else:
                logger.warning("Strikes not found.")
        except Exception as e:
            logger.error(f"Entry Error: {e}")

    async def force_exit(self, reason: str, c_mark: float, p_mark: float):
        if not self.active_trade:
            return
        
        logger.info(f"Closing position: {reason}")
        await self.broker.execute_exit(self.active_trade, c_mark, p_mark, reason, datetime.now(timezone.utc))
        
        # Update DB
        self.db.close_trade(self.active_trade.id, {
            'exit_price_call': c_mark, # Simplified slippage handling
            'exit_price_put': p_mark,
            'exit_reason': reason,
            'pnl': self.active_trade.pnl
        })
        
        await self.notifier.notify_exit(self.active_trade.id, self.active_trade.pnl, reason)
        self.active_trade = None

    async def shutdown(self):
        self.running = False
        await self.notifier.send_message("<b>[SHUTDOWN]</b> Bot stopping gracefully.")
        await self.ws.stop()
