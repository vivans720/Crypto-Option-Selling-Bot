import logging
from datetime import datetime
from typing import List, Dict, Optional
from engine.portfolio import Trade, Portfolio
from config.settings import settings

logger = logging.getLogger(__name__)

class PaperBroker:
    def __init__(self):
        self.portfolio = Portfolio(settings.START_CAPITAL)
        self.slippage_pct = settings.SLIPPAGE_PERCENT
        self.fees_pct = settings.FEES_PERCENT

    async def execute_entry(self, call_inst: dict, put_inst: dict, timestamp: datetime):
        # Simulation of entry with slippage
        # mark_price * (1 - slippage) for selling
        c_price = call_inst['mark_price'] * (1 - self.slippage_pct)
        p_price = put_inst['mark_price'] * (1 - self.slippage_pct)
        
        trade = Trade(
            id=f"live_{timestamp.strftime('%Y%m%d_%H%M')}",
            entry_time=timestamp,
            entry_price_call=c_price,
            entry_price_put=p_price,
            call_strike=call_inst['strike'],
            put_strike=put_inst['strike'],
            qty=1.0,
            call_instrument=call_inst['instrument_name'],
            put_instrument=put_inst['instrument_name']
        )
        self.portfolio.add_trade(trade)
        logger.info(f"Paper Entry: {trade.id} | Call: {trade.call_strike} @ {c_price} | Put: {trade.put_strike} @ {p_price}")
        return trade

    async def execute_exit(self, trade: Trade, call_mark: float, put_mark: float, reason: str, timestamp: datetime):
        # mark_price * (1 + slippage) for buying back
        c_exit = call_mark * (1 + self.slippage_pct)
        p_exit = put_mark * (1 + self.slippage_pct)
        
        trade.close(timestamp, c_exit, p_exit, reason, self.fees_pct)
        logger.info(f"Paper Exit: {trade.id} | Reason: {reason} | PnL: {trade.pnl}")
