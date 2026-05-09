import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import config.settings as settings
from data.ohlcv import fetch_binance_ohlcv
from engine.backtest import BacktestEngine
from analytics.metrics import generate_summary
from analytics.monte_carlo import run_monte_carlo, plot_monte_carlo
from analytics.plots import plot_equity

def inject_extreme_crash(df: pd.DataFrame, drop_pct: float = 0.15, duration_candles: int = 6) -> pd.DataFrame:
    """
    Inject a synthetic extreme crash into the dataset.
    """
    df = df.copy()
    # Pick a random spot in the middle
    crash_idx = len(df) // 2
    
    start_price = df.iloc[crash_idx]['open']
    
    print(f"Injecting {drop_pct*100}% crash at {df.iloc[crash_idx]['timestamp']}")
    
    for i in range(duration_candles):
        idx = crash_idx + i
        if idx >= len(df): break
        
        # Gradually drop price
        factor = 1 - (drop_pct * (i+1) / duration_candles)
        df.loc[df.index[idx], 'open'] = start_price * (1 - (drop_pct * i / duration_candles))
        df.loc[df.index[idx], 'close'] = start_price * factor
        df.loc[df.index[idx], 'high'] = df.loc[df.index[idx], 'open']
        df.loc[df.index[idx], 'low'] = df.loc[df.index[idx], 'close']
        
    return df

def main():
    print("--- STARTING PHASE 4 STRESS TEST ---")
    
    # 1. Fetch 2 Years Data
    end_dt = datetime.utcnow()
    start_dt = end_dt - timedelta(days=365 * 2)
    df = fetch_binance_ohlcv("BTC/USDT", "5m", start_dt, end_dt)
    
    if df.empty: return
    
    # 2. Inject Synthetic Crash (15% in 30 mins)
    df = inject_extreme_crash(df, drop_pct=0.15, duration_candles=6)
    
    # 3. Setup Realistic Config
    # Use best parameters from Phase 3 optimization
    stress_config = {
        'START_CAPITAL': 10000.0,
        'TARGET_DELTA_MIN': 0.15,
        'TARGET_DELTA_MAX': 0.20,
        'SL_MULTIPLIER': 1.5,
        'ENTRY_WINDOW_START': '07:00',
        'ENTRY_WINDOW_END': '09:00',
        'FEES_PERCENT': 0.0003,
        'RISK_FREE_RATE': 0.05,
        'EXIT_TIME': '23:55',
        'SLIPPAGE_PERCENT': 0.01, # 1% base
        'CONSTANT_IV': 0.60,
        'IV_SPIKE_THRESHOLD_PCT': -0.02,
        'IV_PANIC_MULT': 100.0, # Quadratic expansion
        'IV_SPIKE_MULT': 10.0,
        'PUT_SKEW_MULT': 1.20 # Puts 20% more expensive
    }
    
    # 4. Run Realistic Backtest
    print("Running Realistic Backtest (Jumps, Skew, Panic)...")
    engine = BacktestEngine(stress_config)
    engine.run(df)
    
    summary = generate_summary(engine.portfolio)
    
    print("\n--- RESULTS UNDER STRESS ---")
    for k, v in summary.items():
        if not isinstance(v, dict):
            print(f"{k}: {v}")
            
    # 5. Run Monte Carlo
    print("\nRunning Monte Carlo Simulation (10,000 paths)...")
    trades_pnl = [t.pnl for t in engine.portfolio.trades if t.status == 'CLOSED']
    mc_results = run_monte_carlo(trades_pnl, stress_config['START_CAPITAL'])
    
    print("\n--- MONTE CARLO RISK METRICS ---")
    print(f"Probability of Ruin (50% DD): {mc_results['Probability of Ruin (50% DD)']:.2%}")
    print(f"Survival Probability: {mc_results['Survival Probability']:.2%}")
    print(f"Worst-Case Final Equity (5th): ${mc_results['Final Equity 5th']:.2f}")
    print(f"Expected Max Drawdown: {mc_results['Max Drawdown Mean']:.2%}")
    
    # 6. Generate Reports
    plot_equity(engine.portfolio, "stress_test_equity.html")
    plot_monte_carlo(mc_results, "monte_carlo_stress.html")
    print("\nReports generated: stress_test_equity.html, monte_carlo_stress.html")

if __name__ == "__main__":
    main()
