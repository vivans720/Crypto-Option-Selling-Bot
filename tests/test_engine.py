import pytest
from datetime import datetime, timedelta
import pandas as pd
from engine.backtest import BacktestEngine

def test_backtest_engine_synthetic_run():
    config = {
        'START_CAPITAL': 1000,
        'TARGET_DELTA_MIN': 0.1,
        'TARGET_DELTA_MAX': 0.2,
        'ENTRY_WINDOW_START': '08:00',
        'ENTRY_WINDOW_END': '08:05',
        'SL_MULTIPLIER': 2.0,
        'FEES_PERCENT': 0.0,
        'IV_MODE': 'constant',
        'CONSTANT_IV': 0.60
    }
    engine = BacktestEngine(config)
    
    # Create simple OHLCV mock
    base_time = datetime(2023, 1, 1, 7, 50)
    data = []
    for i in range(30):
        t = base_time + timedelta(minutes=i)
        # spot moves up significantly to hit SL
        spot = 40000 + i * 500
        data.append({'timestamp': t, 'close': spot})
        
    df = pd.DataFrame(data)
    engine.run(df)
    
    # Should have entered at 08:00 and exited due to SL later
    assert len(engine.portfolio.trades) == 1
    t = engine.portfolio.trades[0]
    assert t.status == "CLOSED"
    assert t.exit_reason == "COMBINED_SL_HIT"
