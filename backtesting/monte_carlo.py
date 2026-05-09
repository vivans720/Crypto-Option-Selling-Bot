import numpy as np
import pandas as pd
from typing import List
from backtesting.portfolio import Trade

def run_monte_carlo(trades: List[Trade], iterations: int = 1000):
    """Shuffle trade sequences to assess path dependency."""
    if not trades: return None
    
    pnls = np.array([t.pnl for t in trades])
    results = []
    
    for _ in range(iterations):
        shuffled = np.random.choice(pnls, size=len(pnls), replace=True)
        equity = 10000.0 + np.cumsum(shuffled)
        
        final_return = (equity[-1] / 10000.0) - 1
        peak = np.maximum.accumulate(equity)
        max_dd = np.min((equity - peak) / peak)
        
        results.append({
            'final_return': final_return,
            'max_dd': max_dd
        })
        
    return pd.DataFrame(results)
