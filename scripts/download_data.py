import argparse
import sys
from datetime import datetime, timedelta, UTC
from config.settings import settings
from data.ohlcv import fetch_binance_ohlcv

def main():
    parser = argparse.ArgumentParser(description="Download Historical Data into Parquet storage.")
    parser.add_argument("--symbol", type=str, default="BTC/USDT", help="Trading symbol (e.g., BTC/USDT)")
    parser.add_argument("--timeframe", type=str, default="5m", choices=["5m", "15m", "1h", "4h", "1d"], help="Timeframe")
    parser.add_argument("--years", type=float, default=1.0, help="Years of data to download")
    
    args = parser.parse_args()
    
    end_dt = datetime.now(UTC)
    start_dt = end_dt - timedelta(days=int(365 * args.years))
    
    print(f"Downloading {args.symbol} ({args.timeframe}) from {start_dt.date()} to {end_dt.date()}...")
    
    df = fetch_binance_ohlcv(args.symbol, args.timeframe, start_dt, end_dt)
    
    if not df.empty:
        print(f"\nDownload complete! Total candles: {len(df)}")
        print(f"Stored in: {settings.DATA_PARQUET_DIR}")
    else:
        print("\nDownload failed or returned empty dataset.")

if __name__ == "__main__":
    main()
