import logging
from datetime import datetime
from typing import List, Dict, Optional
from engine.portfolio import Trade, Portfolio
from engine.persistence import save_state, load_state

logger = logging.getLogger(__name__)

class PaperBroker:
    def __init__(self, start_capital: float, slippage_pct: float = 0.0025, fees_pct: float = 0.0003):
        self.portfolio = Portfolio(start_capital)
        self.slippage_pct = slippage_pct
        self.fees_pct = fees_pct
        self._load_initial_state()

    def _load_initial_state(self):
        state = load_state()
        if state:
            self.portfolio.capital = state.get('capital', self.portfolio.capital)
            trades_data = state.get('trades', [])
            for t_data in trades_data:
                # Convert string timestamps back to datetime
                if isinstance(t_data.get('entry_time'), str):
                    t_data['entry_time'] = datetime.fromisoformat(t_data['entry_time'])
                if isinstance(t_data.get('exit_time'), str):
                    t_data['exit_time'] = datetime.fromisoformat(t_data['exit_time'])
                
                trade = Trade(**t_data)
                self.portfolio.add_trade(trade)
            logger.info(f"PaperBroker state loaded with {len(self.portfolio.trades)} trades.")

    def sync_state(self):
        state = {
            'capital': self.portfolio.capital,
            'trades': [vars(t) for t in self.portfolio.trades],
            'last_sync': datetime.now().isoformat()
        }
        save_state(state)

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
            qty=1.0 # Default 1 BTC for now
        )
        self.portfolio.add_trade(trade)
        self.sync_state()
        logger.info(f"Paper Entry: {trade.id} | Call: {trade.call_strike} @ {c_price} | Put: {trade.put_strike} @ {p_price}")
        return trade

    async def execute_exit(self, trade: Trade, call_mark: float, put_mark: float, reason: str, timestamp: datetime):
        # mark_price * (1 + slippage) for buying back
        c_exit = call_mark * (1 + self.slippage_pct)
        p_exit = put_mark * (1 + self.slippage_pct)
        
        trade.close(timestamp, c_exit, p_exit, reason, self.fees_pct)
        self.sync_state()
        logger.info(f"Paper Exit: {trade.id} | Reason: {reason} | PnL: {trade.pnl}")
