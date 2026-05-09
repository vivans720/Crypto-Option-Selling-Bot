import pytest
from unittest.mock import patch
import pandas as pd
from datetime import datetime
from data.ohlcv import fetch_binance_ohlcv

@patch('ccxt.binance')
def test_fetch_binance_ohlcv(mock_binance):
    mock_exchange = mock_binance.return_value
    
    # Mock return 2 candles
    mock_exchange.fetch_ohlcv.side_effect = [
        [
            [1672531200000, 16500, 16600, 16400, 16550, 1000],
            [1672534800000, 16550, 16650, 16500, 16600, 1200]
        ],
        [] # Stop loop
    ]
    
    start = datetime(2023, 1, 1)
    end = datetime(2023, 1, 2)
    
    df = fetch_binance_ohlcv("BTC/USDT", "1h", start, end)
    
    assert not df.empty
    assert len(df) == 2
    assert 'close' in df.columns
    assert df.iloc[0]['close'] == 16550
