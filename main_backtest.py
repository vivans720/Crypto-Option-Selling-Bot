import pandas as pd
from datetime import datetime, timedelta, UTC
from config.settings import settings
from data.ohlcv import fetch_binance_ohlcv
from backtesting.engine import BacktestEngine
from backtesting.models import ExecutionConfig
from backtesting.metrics import generate_summary
from backtesting.monte_carlo import run_monte_carlo
from visualization.reporting import plot_performance_dashboard, plot_monthly_heatmap
from py_vollib.black_scholes import black_scholes

def main():
    print("Starting Professional Crypto Options Research Engine...")
    
    # 1. Config & Models
    config = {
        'START_CAPITAL': settings.START_CAPITAL,
        'TARGET_DELTA_MIN': settings.TARGET_DELTA_MIN,
        'TARGET_DELTA_MAX': settings.TARGET_DELTA_MAX,
        'ENTRY_WINDOW_START': '07:00',
        'ENTRY_WINDOW_END': '09:00',
        'SL_MULTIPLIER': settings.SL_MULTIPLIER,
        'RISK_FREE_RATE': 0.05,
        'EXIT_TIME': '23:55'
    }
    
    exec_config = ExecutionConfig(
        maker_fee=0.0002,
        taker_fee=0.0005,
        fixed_slippage=0.0005
    )
    
    engine = BacktestEngine(config, exec_config)
    
    # 2. Data Acquisition (Large Dataset Test)
    end_dt = datetime.now(UTC)
    start_dt = end_dt - timedelta(days=30) # 1 month for demo
    
    print(f"Fetching BTC/USDT 5m data from {start_dt.date()} to {end_dt.date()}...")
    ohlcv_df = fetch_binance_ohlcv("BTC/USDT", "5m", start_dt, end_dt)
    
    if ohlcv_df.empty:
        print("No data found.")
        return
        
    print(f"Loaded {len(ohlcv_df)} candles. Running simulation...")
    engine.run(ohlcv_df)
    
    # 3. Finalize Trades
    for t in engine.portfolio.get_open_trades():
        last_row = ohlcv_df.iloc[-1]
        t.close(last_row.timestamp, t.entry_price_call, t.entry_price_put, "END_OF_TEST", 0)
        
    # 4. Analysis & Reporting
    print("\n" + "="*30)
    print("PERFORMANCE SUMMARY")
    print("="*30)
    summary = generate_summary(engine.portfolio)
    for k, v in summary.items():
        if isinstance(v, float):
            print(f"{k:<20}: {v:>10.4f}")
        else:
            print(f"{k:<20}: {v}")
            
    # 5. Export Results
    reports_dir = settings.RESEARCH_REPORTS_DIR
    results_dir = settings.RESEARCH_RESULTS_DIR
    
    plot_performance_dashboard(engine.portfolio, reports_dir)
    
    if engine.portfolio.trades:
        df_trades = pd.DataFrame([vars(t) for t in engine.portfolio.trades])
        trade_log = results_dir / "backtest_trades.parquet"
        df_trades.to_parquet(trade_log)
        print(f"Trade log: {trade_log}")
        
        # Monte Carlo
        print("\nRunning Monte Carlo (1000 paths)...")
        mc_results = run_monte_carlo(engine.portfolio.trades)
        if mc_results is not None:
            mc_results.to_parquet(results_dir / "monte_carlo.parquet")
            print(f"VaR 95%: {mc_results['final_return'].quantile(0.05):.2%}")

if __name__ == "__main__":
    main()
