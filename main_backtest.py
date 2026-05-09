import pandas as pd
from datetime import datetime, timedelta
from config.settings import settings
from data.ohlcv import fetch_binance_ohlcv
from backtesting.engine import BacktestEngine
from backtesting.metrics import generate_summary
from visualization.equity_curve import plot_equity
from py_vollib.black_scholes import black_scholes

def main():
    print("Starting Crypto Synthetic Options Backtester...")
    
    # Configuration
    config = {
        'START_CAPITAL': settings.START_CAPITAL,
        'TARGET_DELTA_MIN': settings.TARGET_DELTA_MIN,
        'TARGET_DELTA_MAX': settings.TARGET_DELTA_MAX,
        'ENTRY_WINDOW_START': '07:00',
        'ENTRY_WINDOW_END': '09:00',
        'SL_MULTIPLIER': settings.SL_MULTIPLIER,
        'FEES_PERCENT': settings.FEES_PERCENT,
        'IV_MODE': 'constant',
        'CONSTANT_IV': 0.60,
        'RISK_FREE_RATE': 0.05,
        'EXIT_TIME': '23:55'
    }
    
    engine = BacktestEngine(config)
    
    # Fetch 7 days of historical 5m data for MVP test
    end_dt = datetime.utcnow()
    start_dt = end_dt - timedelta(days=7)
    
    print(f"Fetching Binance BTC/USDT 5m candles from {start_dt.date()} to {end_dt.date()}...")
    try:
        ohlcv_df = fetch_binance_ohlcv("BTC/USDT", "5m", start_dt, end_dt)
        print(f"Fetched {len(ohlcv_df)} candles.")
    except Exception as e:
        print(f"Error fetching data: {e}")
        return
        
    if ohlcv_df.empty:
        print("No data fetched.")
        return
        
    print("Running Backtest simulation (candle-by-candle)...")
    engine.run(ohlcv_df)
    
    # Finalize any open trades at the end of the simulation
    open_trades = engine.portfolio.get_open_trades()
    for t in open_trades:
        last_spot = ohlcv_df.iloc[-1]['close']
        last_ts = ohlcv_df.iloc[-1]['timestamp']
        c_mark = black_scholes('c', last_spot, t.call_strike, 1.0/365.0, config['RISK_FREE_RATE'], config['CONSTANT_IV'])
        p_mark = black_scholes('p', last_spot, t.put_strike, 1.0/365.0, config['RISK_FREE_RATE'], config['CONSTANT_IV'])
        
        t.close(last_ts, c_mark, p_mark, "END_OF_BACKTEST", config['FEES_PERCENT'])
        
    print("\n--- Backtest Complete ---")
    summary = generate_summary(engine.portfolio)
    for k, v in summary.items():
        print(f"{k}: {v}")
        
    if engine.portfolio.trades:
        df_trades = pd.DataFrame([vars(t) for t in engine.portfolio.trades])
        log_path = settings.DATA_EXPORTS_DIR / "trade_log.csv"
        df_trades.to_csv(log_path, index=False)
        print(f"Trade log saved to {log_path}")
        
    plot_equity(engine.portfolio)

if __name__ == "__main__":
    main()
