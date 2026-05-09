import ccxt
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, UTC
import os
from tqdm import tqdm
from data.storage import save_parquet, load_parquet
from config.settings import settings

def validate_ohlcv(df: pd.DataFrame, timeframe: str) -> pd.DataFrame:
    """Check for missing candles and duplicates."""
    if df.empty:
        return df
    
    df = df.drop_duplicates(subset=['timestamp']).sort_values('timestamp')
    
    # Check for gaps
    time_diff = df['timestamp'].diff().median()
    gaps = df['timestamp'].diff() > time_diff
    if gaps.any():
        num_gaps = gaps.sum()
        print(f"Warning: Detected {num_gaps} gaps in data.")
        
    return df

def fetch_binance_ohlcv(symbol: str, timeframe: str, start_dt: datetime, end_dt: datetime) -> pd.DataFrame:
    """
    Fetch historical OHLCV data from Binance with chunking.
    Uses local .parquet cache in data/cache.
    """
    safe_symbol = symbol.replace("/", "_")
    cache_file = settings.DATA_CACHE_DIR / f"{safe_symbol}_{timeframe}_{start_dt.strftime('%Y%m%d')}_{end_dt.strftime('%Y%m%d')}.parquet"
    
    cached_df = load_parquet(cache_file)
    if cached_df is not None:
        print(f"Loading from cache: {cache_file}")
        return cached_df
        
    exchange = ccxt.binance({'enableRateLimit': True})
    all_ohlcv = []
    
    # Chunking: Fetch in 7-day blocks to prevent massive single requests
    chunk_size = timedelta(days=7)
    current_start = start_dt
    
    total_days = (end_dt - start_dt).days
    pbar = tqdm(total=total_days, desc=f"Downloading {symbol}")

    while current_start < end_dt:
        current_end = min(current_start + chunk_size, end_dt)
        since = int(current_start.timestamp() * 1000)
        
        while since < int(current_end.timestamp() * 1000):
            try:
                ohlcv = exchange.fetch_ohlcv(symbol, timeframe, since=since, limit=1000)
                if not ohlcv:
                    break
                all_ohlcv.extend(ohlcv)
                since = ohlcv[-1][0] + 1
            except Exception as e:
                print(f"Error at {current_start}: {e}. Retrying...")
                import time
                time.sleep(2)
                continue
        
        current_start = current_end
        pbar.update(7 if current_start < end_dt else total_days % 7)
            
    pbar.close()
    
    if not all_ohlcv:
        return pd.DataFrame()
        
    df = pd.DataFrame(all_ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms', utc=True)
    
    df = df[(df['timestamp'] >= start_dt) & (df['timestamp'] <= end_dt)]
    df = validate_ohlcv(df, timeframe)
    
    save_parquet(df, cache_file)
    return df
