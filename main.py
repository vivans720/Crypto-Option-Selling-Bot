import pandas as pd
from datetime import datetime, timedelta
import config.settings as settings
from data.ohlcv import fetch_binance_ohlcv
from engine.backtest import BacktestEngine
from analytics.metrics import generate_summary
from analytics.plots import plot_equity

def main():
    print("Starting Crypto Synthetic Options Backtester...")
    
    # Configuration
    config = {
        'START_CAPITAL': settings.START_CAPITAL,
        'TARGET_DELTA_MIN': settings.TARGET_DELTA_MIN,
        'TARGET_DELTA_MAX': settings.TARGET_DELTA_MAX,
        'ENTRY_WINDOW_START': settings.ENTRY_WINDOW_START,
        'ENTRY_WINDOW_END': settings.ENTRY_WINDOW_END,
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
        # Close at last candle's spot price
        last_spot = ohlcv_df.iloc[-1]['close']
        last_ts = ohlcv_df.iloc[-1]['timestamp']
        from pricing.bs_model import calc_option_price
        c_mark = calc_option_price(last_spot, t.call_strike, 1.0/365.0, config['RISK_FREE_RATE'], config['CONSTANT_IV'], 'call')
        p_mark = calc_option_price(last_spot, t.put_strike, 1.0/365.0, config['RISK_FREE_RATE'], config['CONSTANT_IV'], 'put')
        
        t.close(last_ts, c_mark, p_mark, "END_OF_BACKTEST", config['FEES_PERCENT'])
        
    print("\n--- Backtest Complete ---")
    summary = generate_summary(engine.portfolio)
    for k, v in summary.items():
        print(f"{k}: {v}")
        
    if engine.portfolio.trades:
        df_trades = pd.DataFrame([vars(t) for t in engine.portfolio.trades])
        df_trades.to_csv("trade_log.csv", index=False)
        print("Trade log saved to trade_log.csv")
        
    plot_equity(engine.portfolio)

if __name__ == "__main__":
    main()
