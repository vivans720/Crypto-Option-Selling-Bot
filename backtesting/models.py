from dataclasses import dataclass
from enum import Enum
import numpy as np

class FeeType(Enum):
    MAKER = "maker"
    TAKER = "taker"

@dataclass
class ExecutionConfig:
    maker_fee: float = 0.0002
    taker_fee: float = 0.0005
    fixed_slippage: float = 0.0001
    vol_multiplier: float = 2.0
    liquidity_cap_pct: float = 0.1  # Max % of candle volume
    maintenance_margin_pct: float = 0.05
    liquidation_threshold_pct: float = 0.03

def calculate_slippage(base_slippage: float, vol_ratio: float, config: ExecutionConfig) -> float:
    """Volatility-adjusted slippage."""
    return base_slippage * (1 + (vol_ratio * config.vol_multiplier))

def check_liquidation(equity: float, margin_used: float, config: ExecutionConfig) -> bool:
    """Check if position should be liquidated."""
    if margin_used <= 0:
        return False
    return (equity / margin_used) < (1 + config.liquidation_threshold_pct)
