from typing import List, Optional
from dataclasses import dataclass, field
import datetime

@dataclass
class Trade:
    id: str
    entry_time: datetime.datetime
    entry_price_call: float
    entry_price_put: float
    call_strike: float
    put_strike: float
    qty: float
    status: str = "OPEN" # OPEN, CLOSED
    exit_time: Optional[datetime.datetime] = None
    exit_price_call: Optional[float] = None
    exit_price_put: Optional[float] = None
    exit_reason: Optional[str] = None
    pnl: float = 0.0
    
    def close(self, exit_time: datetime.datetime, exit_call: float, exit_put: float, reason: str, fees_percent: float):
        self.exit_time = exit_time
        self.exit_price_call = exit_call
        self.exit_price_put = exit_put
        self.exit_reason = reason
        self.status = "CLOSED"
        
        # PnL calculation for short options
        # We sold at entry, bought at exit. 
        call_pnl = (self.entry_price_call - self.exit_price_call) * self.qty
        put_pnl = (self.entry_price_put - self.exit_price_put) * self.qty
        
        # Deduct fees (fee applies to both legs, entry and exit based on underlying qty/notional, simplified here to premium % for MVP)
        # Assuming fees_percent is applied to total entry/exit premium
        entry_fees = (self.entry_price_call + self.entry_price_put) * self.qty * fees_percent
        exit_fees = (self.exit_price_call + self.exit_price_put) * self.qty * fees_percent
        
        self.pnl = call_pnl + put_pnl - entry_fees - exit_fees

class Portfolio:
    def __init__(self, start_capital: float):
        self.capital = start_capital
        self.equity_curve: List[dict] = []
        self.trades: List[Trade] = []
        
    @property
    def equity_history(self):
        return self.equity_curve
        
    @property
    def current_equity(self) -> float:
        if not self.equity_curve:
            return self.capital + sum(t.pnl for t in self.trades if t.status == "CLOSED")
        return self.equity_curve[-1]['equity']
        
    def add_trade(self, trade: Trade):
        self.trades.append(trade)
        
    def get_open_trades(self) -> List[Trade]:
        return [t for t in self.trades if t.status == "OPEN"]
        
    def record_equity(self, timestamp: datetime.datetime, open_pnl: float = 0.0):
        total_equity = self.capital + sum(t.pnl for t in self.trades if t.status == "CLOSED") + open_pnl
        self.equity_curve.append({
            'timestamp': timestamp,
            'equity': total_equity
        })
