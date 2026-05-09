import asyncio
import logging
from datetime import datetime, time
import config.settings as settings
from api.websocket_client import DeribitWebsocketClient
from api.deribit import fetch_option_chain
from api.notifications import TelegramNotifier
from engine.paper_broker import PaperBroker
from strategy.core import select_strikes, calculate_exit

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LiveEngine:
    def __init__(self, testnet: bool = True):
        self.broker = PaperBroker(settings.START_CAPITAL, settings.SLIPPAGE_PERCENT, settings.FEES_PERCENT)
        self.ws = DeribitWebsocketClient(testnet=testnet)
        self.notifier = TelegramNotifier(settings.TELEGRAM_BOT_TOKEN, settings.TELEGRAM_CHAT_ID)
        
        # Load active trade from broker if exists
        open_trades = self.broker.portfolio.get_open_trades()
        self.active_trade = open_trades[0] if open_trades else None
        self.prices = {} # Latest mark prices

    async def _on_ticker(self, data):
        instrument = data['instrument_name']
        self.prices[instrument] = data['mark_price']
        
        if self.active_trade and self.active_trade.status == "OPEN":
            await self.check_exits()

    async def check_exits(self):
        if not self.active_trade or self.active_trade.status != "OPEN":
            return

        c_inst = f"BTC-{self.active_trade.entry_time.strftime('%d%b%y').upper()}-{int(self.active_trade.call_strike)}-C"
        p_inst = f"BTC-{self.active_trade.entry_time.strftime('%d%b%y').upper()}-{int(self.active_trade.put_strike)}-P"
        
        c_mark = self.prices.get(c_inst)
        p_mark = self.prices.get(p_inst)

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
                await self.broker.execute_exit(self.active_trade, c_mark, p_mark, exit_reason, datetime.now())
                await self.notifier.notify_exit(self.active_trade.id, self.active_trade.pnl, exit_reason)
                self.active_trade = None

    async def run_daily_loop(self):
        await self.ws.connect()
        # Start listening in background
        asyncio.create_task(self.ws.listen())

        while True:
            now = datetime.now()
            current_time = now.strftime("%H:%M")
            
            # 1. Entry Window
            if settings.ENTRY_WINDOW_START <= current_time <= settings.ENTRY_WINDOW_END:
                if not self.active_trade or self.active_trade.status == "CLOSED":
                    await self.attempt_entry(now)
            
            # 2. Expiry Check (Simplified: close at 23:55)
            if current_time >= "23:55" and self.active_trade and self.active_trade.status == "OPEN":
                await self.force_exit("EXPIRY")

            # 3. Heartbeat (Every hour at :00)
            if now.minute == 0 and now.second < 60:
                await self.notifier.send_message(f"<b>[HEARTBEAT]</b>\nSystem live.\nTime: {current_time}")

            await asyncio.sleep(60) # Check every minute

    async def attempt_entry(self, now: datetime):
        logger.info("Attempting entry...")
        try:
            chain = fetch_option_chain(settings.TRADING_SYMBOL)
            strikes = select_strikes(chain, settings.TARGET_DELTA_MIN, settings.TARGET_DELTA_MAX)
            
            if strikes['call'] and strikes['put']:
                self.active_trade = await self.broker.execute_entry(strikes['call'], strikes['put'], now)
                
                # Notify
                total_prem = strikes['call']['mark_price'] + strikes['put']['mark_price']
                await self.notifier.notify_entry(
                    self.active_trade.id, 
                    strikes['call'].get('spot_price', 0), # spot_price might be in chain
                    strikes['call']['strike'], 
                    strikes['put']['strike'], 
                    total_prem
                )
                
                # Subscribe to tickers for these instruments
                channels = [
                    f"ticker.{strikes['call']['instrument_name']}.raw",
                    f"ticker.{strikes['put']['instrument_name']}.raw"
                ]
                await self.ws.subscribe(channels, self._on_ticker)
            else:
                logger.warning("Could not find matching strikes.")
        except Exception as e:
            logger.error(f"Entry Error: {e}")

    async def force_exit(self, reason: str):
        # Implementation to close trade using latest prices
        pass

if __name__ == "__main__":
    engine = LiveEngine(testnet=False)
    asyncio.run(engine.run_daily_loop())
