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
    call_instrument: str = ""
    put_instrument: str = ""
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
        
        # PnL for short options: (Sold - Bought)
        call_pnl = (self.entry_price_call - self.exit_price_call) * self.qty
        put_pnl = (self.entry_price_put - self.exit_price_put) * self.qty
        
        # Fees on notional or premium? Simplified to premium % for paper trading
        entry_fees = (self.entry_price_call + self.entry_price_put) * self.qty * fees_percent
        exit_fees = (self.exit_price_call + self.exit_price_put) * self.qty * fees_percent
        
        self.pnl = call_pnl + put_pnl - entry_fees - exit_fees

class Portfolio:
    def __init__(self, start_capital: float):
        self.capital = start_capital
        self.equity_curve: List[dict] = []
        self.trades: List[Trade] = []
        
    @property
    def current_equity(self) -> float:
        return self.capital + sum(t.pnl for t in self.trades if t.status == "CLOSED")
        
    def add_trade(self, trade: Trade):
        self.trades.append(trade)
        
    def get_open_trades(self) -> List[Trade]:
        return [t for t in self.trades if t.status == "OPEN"]
