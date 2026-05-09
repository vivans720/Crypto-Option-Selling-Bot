import ccxt
import pandas as pd
from datetime import datetime
import os
from tqdm import tqdm

def fetch_binance_ohlcv(symbol: str, timeframe: str, start_dt: datetime, end_dt: datetime) -> pd.DataFrame:
    """
    Fetch historical OHLCV data from Binance. 
    Uses local .parquet cache to avoid hitting rate limits.
    """
    cache_dir = "cache"
    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir)
        
    safe_symbol = symbol.replace("/", "_")
    cache_file = os.path.join(cache_dir, f"{safe_symbol}_{timeframe}_{start_dt.strftime('%Y%m%d')}_{end_dt.strftime('%Y%m%d')}.parquet")
    
    if os.path.exists(cache_file):
        print(f"Loading {symbol} data from cache: {cache_file}")
        return pd.read_parquet(cache_file)
        
    print(f"Cache miss. Fetching {symbol} from Binance via CCXT...")
    exchange = ccxt.binance({'enableRateLimit': True})
    
    start_ts = int(start_dt.timestamp() * 1000)
    end_ts = int(end_dt.timestamp() * 1000)
    
    all_ohlcv = []
    current_ts = start_ts
    
    # Calculate estimated iterations for tqdm
    # 5m = 300000 ms
    timeframe_ms = exchange.parse_timeframe(timeframe) * 1000
    total_candles = (end_ts - start_ts) // timeframe_ms
    estimated_requests = total_candles // 1000 + 1
    
    pbar = tqdm(total=estimated_requests, desc=f"Downloading {symbol} {timeframe}")
    
    while current_ts < end_ts:
        try:
            ohlcv = exchange.fetch_ohlcv(symbol, timeframe, since=current_ts, limit=1000)
        except Exception as e:
            print(f"Fetch error: {e}. Retrying after sleep...")
            import time
            time.sleep(5)
            continue
            
        if not ohlcv:
            break
            
        all_ohlcv.extend(ohlcv)
        current_ts = ohlcv[-1][0] + 1
        pbar.update(1)
        
        # If we got less than 1000, we probably reached current time
        if len(ohlcv) < 1000:
            break
            
    pbar.close()
    
    if not all_ohlcv:
        print("No data fetched!")
        return pd.DataFrame()
        
    df = pd.DataFrame(all_ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    
    # Filter strictly between start_dt and end_dt
    df = df[(df['timestamp'] >= start_dt) & (df['timestamp'] <= end_dt)]
    
    # Cache to parquet
    print(f"Saving {len(df)} rows to {cache_file}...")
    df.to_parquet(cache_file, index=False)
    
    return df
