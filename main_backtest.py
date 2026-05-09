import pandas as pd
import argparse
from datetime import datetime, timedelta, UTC
from config.settings import settings
from data.ohlcv import fetch_binance_ohlcv
from backtesting.engine import BacktestEngine
from backtesting.models import ExecutionConfig
from backtesting.metrics import generate_summary
from backtesting.monte_carlo import run_monte_carlo
from visualization.reporting import plot_performance_dashboard, plot_monthly_heatmap, plot_yearly_stats
from py_vollib.black_scholes import black_scholes

def parse_args():
    parser = argparse.ArgumentParser(description="Professional Crypto Options Research Engine")
    parser.add_argument("--symbol", type=str, default="BTC/USDT", help="Trading pair (default: BTC/USDT)")
    parser.add_argument("--timeframe", type=str, default="5m", help="Candle timeframe (default: 5m)")
    parser.add_argument("--start", type=str, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end", type=str, help="End date (YYYY-MM-DD)")
    parser.add_argument("--years", type=float, help="Number of years to backtest")
    return parser.parse_args()

def main():
    print("Starting Professional Crypto Options Research Engine...")
    args = parse_args()
    
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
    
    # 2. Data Acquisition
    end_dt = datetime.strptime(args.end, "%Y-%m-%d").replace(tzinfo=UTC) if args.end else datetime.now(UTC)
    
    if args.start:
        start_dt = datetime.strptime(args.start, "%Y-%m-%d").replace(tzinfo=UTC)
    elif args.years:
        start_dt = end_dt - timedelta(days=int(365.25 * args.years))
    else:
        start_dt = end_dt - timedelta(days=30)
    
    print(f"Fetching {args.symbol} {args.timeframe} data from {start_dt.date()} to {end_dt.date()}...")
    ohlcv_df = fetch_binance_ohlcv(args.symbol, args.timeframe, start_dt, end_dt)
    
    if ohlcv_df.empty:
        print("No data found.")
        return
        
    total_candles = len(ohlcv_df)
    print(f"Loaded {total_candles} candles. Running simulation...")
    engine.run(ohlcv_df)
    
    # 3. Finalize Trades
    for t in engine.portfolio.get_open_trades():
        last_row = ohlcv_df.iloc[-1]
        t.close(last_row.timestamp, t.entry_price_call, t.entry_price_put, "END_OF_TEST", 0)
        
    from backtesting.regimes import classify_regimes
    
    # 4. Analysis & Reporting
    summary = generate_summary(engine.portfolio)
    
    print("\n" + "="*30)
    print("BACKTEST PERIOD SUMMARY")
    print("="*30)
    total_days = (end_dt - start_dt).days or 1
    total_trades = summary.get('Total Trades', 0)
    trades_per_month = total_trades / (total_days / 30.44) if total_days > 0 else 0
    
    print(f"Start Date          : {start_dt.date()}")
    print(f"End Date            : {end_dt.date()}")
    print(f"Total Days          : {total_days}")
    print(f"Total Candles       : {total_candles}")
    print(f"Total Trades        : {total_trades}")
    print(f"Trades Per Month    : {trades_per_month:.1f}")
    
    print("\n" + "="*30)
    print("PERFORMANCE SUMMARY")
    print("="*30)
    
    for k, v in summary.items():
        if isinstance(v, float):
            print(f"{k:<20}: {v:>10.4f}")
        else:
            print(f"{k:<20}: {v}")
            
    reports_dir = settings.RESEARCH_REPORTS_DIR
    results_dir = settings.RESEARCH_RESULTS_DIR
    reports_dir.mkdir(parents=True, exist_ok=True)
    results_dir.mkdir(parents=True, exist_ok=True)
    
    print("\n" + "="*30)
    print("REGIME ANALYSIS")
    print("="*30)
    regimes_df = classify_regimes(ohlcv_df, engine.portfolio)
    if not regimes_df.empty:
        regime_summary = regimes_df.groupby('trend').apply(
            lambda x: pd.Series({
                'Trades': len(x),
                'Win Rate': (x['pnl'] > 0).mean(),
                'Net PnL': x['pnl'].sum(),
                'Drawdown': x['drawdown'].min() if 'drawdown' in x.columns else 0.0
            })
        ).reset_index()
        
        print("| Regime | Trades | Win Rate | Net PnL | Drawdown |")
        print("-" * 55)
        for _, row in regime_summary.iterrows():
            print(f"| {row['trend']:<6} | {int(row['Trades']):<6} | {row['Win Rate']:.1%} | {row['Net PnL']:>7.2f} | {row['Drawdown']:.2%} |")
            
        # Volatility regimes
        vol_summary = regimes_df.groupby('vol_regime').apply(
            lambda x: pd.Series({
                'Trades': len(x),
                'Win Rate': (x['pnl'] > 0).mean(),
                'Net PnL': x['pnl'].sum(),
                'Drawdown': x['drawdown'].min() if 'drawdown' in x.columns else 0.0
            })
        ).reset_index()
        for _, row in vol_summary.iterrows():
            print(f"| {row['vol_regime']:<6} | {int(row['Trades']):<6} | {row['Win Rate']:.1%} | {row['Net PnL']:>7.2f} | {row['Drawdown']:.2%} |")

        regimes_df.to_parquet(results_dir / "regime_analysis.parquet")
            
    # 5. Export Results
    plot_performance_dashboard(engine.portfolio, reports_dir)
    df_eq = pd.DataFrame(engine.portfolio.equity_history, columns=['timestamp', 'equity']).set_index('timestamp')
    plot_monthly_heatmap(df_eq['equity'], reports_dir)
    plot_yearly_stats(engine.portfolio, reports_dir)
    
    if engine.portfolio.trades:
        df_trades = pd.DataFrame([vars(t) for t in engine.portfolio.trades])
        trade_log = results_dir / "backtest_trades.parquet"
        df_trades.to_parquet(trade_log)
        print(f"\nTrade log: {trade_log}")
        
        # Monte Carlo
        print("\nRunning Monte Carlo (1000 paths)...")
        mc_results = run_monte_carlo(engine.portfolio.trades)
        if mc_results is not None:
            mc_results.to_parquet(results_dir / "monte_carlo.parquet")
            var_95 = mc_results['final_return'].quantile(0.05)
            var_99 = mc_results['final_return'].quantile(0.01)
            
            prob_ls_5 = (mc_results['max_losing_streak'] > 5).mean()
            
            print(f"VaR 95%: {var_95:.2%}")
            print(f"VaR 99%: {var_99:.2%}")
            print(f"Prob(Losing Streak > 5): {prob_ls_5:.2%}")

if __name__ == "__main__":
    main()
