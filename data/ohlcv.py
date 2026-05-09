import ccxt
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, UTC
import os
from tqdm import tqdm
from data.storage import save_parquet, load_parquet, append_parquet
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
    Uses local .parquet cache in data/parquet/{exchange}/{symbol}/{timeframe}/data.parquet.
    """
    safe_symbol = symbol.replace("/", "_")
    data_dir = settings.DATA_PARQUET_DIR / "binance" / safe_symbol / timeframe
    data_dir.mkdir(parents=True, exist_ok=True)
    cache_file = data_dir / "data.parquet"
    
    exchange = ccxt.binance({'enableRateLimit': True})
    
    # Determine the actual ranges we need to fetch
    fetch_start = start_dt
    fetch_end = end_dt
    
    cached_df = load_parquet(cache_file)
    if cached_df is not None and not cached_df.empty:
        min_cached = cached_df['timestamp'].min()
        max_cached = cached_df['timestamp'].max()
        
        if start_dt >= min_cached and end_dt <= max_cached:
            print(f"Data completely cached in {cache_file}.")
            df = cached_df[(cached_df['timestamp'] >= start_dt) & (cached_df['timestamp'] <= end_dt)]
            return validate_ohlcv(df, timeframe)
        
        # Determine if we only need to append at the end
        if start_dt >= min_cached and end_dt > max_cached:
            fetch_start = max_cached
            print(f"Partial cache found. Fetching missing data from {fetch_start} to {fetch_end}...")
        # Determine if we only need to prepend at the start
        elif end_dt <= max_cached and start_dt < min_cached:
            fetch_end = min_cached
            print(f"Partial cache found. Fetching missing data from {fetch_start} to {fetch_end}...")
        else:
            print(f"Fetching data from {fetch_start} to {fetch_end}...")
            
    else:
        print(f"No cache found. Fetching data from {fetch_start} to {fetch_end}...")

    # Chunking: Fetch in 30-day blocks to append incrementally
    chunk_size = timedelta(days=30)
    current_start = fetch_start
    total_days = (fetch_end - fetch_start).days
    
    if total_days > 0:
        pbar = tqdm(total=total_days, desc=f"Downloading {symbol}")

        while current_start < fetch_end:
            current_end = min(current_start + chunk_size, fetch_end)
            since = int(current_start.timestamp() * 1000)
            
            chunk_ohlcv = []
            while since < int(current_end.timestamp() * 1000):
                try:
                    ohlcv = exchange.fetch_ohlcv(symbol, timeframe, since=since, limit=1000)
                    if not ohlcv:
                        break
                    chunk_ohlcv.extend(ohlcv)
                    since = ohlcv[-1][0] + 1
                except Exception as e:
                    print(f"Error at {datetime.fromtimestamp(since/1000, tz=UTC)}: {e}. Retrying...")
                    import time
                    time.sleep(2)
                    continue
            
            if chunk_ohlcv:
                df_chunk = pd.DataFrame(chunk_ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                df_chunk['timestamp'] = pd.to_datetime(df_chunk['timestamp'], unit='ms', utc=True)
                append_parquet(df_chunk, cache_file)
            
            days_fetched = (current_end - current_start).days
            pbar.update(days_fetched if days_fetched > 0 else 1)
            current_start = current_end
                
        pbar.close()
    
    # Reload final combined parquet
    final_df = load_parquet(cache_file)
    if final_df is None or final_df.empty:
        return pd.DataFrame()
        
    df = final_df[(final_df['timestamp'] >= start_dt) & (final_df['timestamp'] <= end_dt)].copy()
    return validate_ohlcv(df, timeframe)
