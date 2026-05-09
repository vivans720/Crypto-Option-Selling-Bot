import pandas as pd
from datetime import datetime, timedelta
import config.settings as settings
from data.ohlcv import fetch_binance_ohlcv
from engine.optimizer import GridSearchOptimizer
from analytics.plots import generate_optimization_heatmap

def main():
    print("Starting Optimization Module...")
    
    # 2 Years of data
    end_dt = datetime.utcnow()
    start_dt = end_dt - timedelta(days=365 * 2)
    
    print(f"Fetching Binance BTC/USDT 5m candles from {start_dt.date()} to {end_dt.date()}...")
    try:
        df = fetch_binance_ohlcv("BTC/USDT", "5m", start_dt, end_dt)
    except Exception as e:
        print(f"Error fetching data: {e}")
        return
        
    if df.empty:
        print("No data available.")
        return
        
    base_config = {
        'START_CAPITAL': settings.START_CAPITAL,
        'ENTRY_WINDOW_START': settings.ENTRY_WINDOW_START,
        'ENTRY_WINDOW_END': settings.ENTRY_WINDOW_END,
        'FEES_PERCENT': settings.FEES_PERCENT,
        'RISK_FREE_RATE': 0.05,
        'EXIT_TIME': '23:55',
        'SLIPPAGE_PERCENT': 0.01, # 1% slippage
        'IV_SPIKE_THRESHOLD_PCT': -0.02, # -2% drop in 1h spikes IV
        'IV_SPIKE_MULTIPLIER': 10.0
    }
    
    param_grid = {
        'TARGET_DELTA_MIN': [0.05, 0.10, 0.15],
        'TARGET_DELTA_MAX': [0.10, 0.15, 0.20],
        'SL_MULTIPLIER': [1.5, 2.0, 3.0],
        # Only valid delta ranges: min < max
    }
    
    # Filter invalid delta combinations from grid conceptually or let the engine handle it.
    # To keep the grid clean, we construct the grid manually for delta:
    delta_pairs = [(0.05, 0.10), (0.10, 0.15), (0.15, 0.20)]
    
    actual_grid = {
        'delta_pair': delta_pairs,
        'SL_MULTIPLIER': [1.5, 2.0, 3.0]
    }
    
    # We will pass a slightly modified dict and unpack it in the worker, or just map it in param_grid.
    # For simplicity, let's redefine the param grid flat.
    flat_grid = {
        'TARGET_DELTA_MIN': [0.05, 0.10, 0.15],
        'SL_MULTIPLIER': [1.5, 2.0, 3.0]
    }
    # In run_single_backtest, TARGET_DELTA_MAX can be TARGET_DELTA_MIN + 0.05. We'll do this to keep grid small for the MVP.
    
    # Overwrite param grid properly:
    def param_generator():
        for d_min in [0.05, 0.10, 0.15]:
            for sl in [1.5, 2.0, 3.0]:
                yield {
                    'TARGET_DELTA_MIN': d_min,
                    'TARGET_DELTA_MAX': d_min + 0.05,
                    'SL_MULTIPLIER': sl
                }
                
    # To conform to GridSearchOptimizer, we pass param_grid:
    # Actually, GridSearchOptimizer uses itertools.product.
    # We can pass valid grid:
    valid_grid = {
        'TARGET_DELTA_MIN': [0.05, 0.10, 0.15],
        'SL_MULTIPLIER': [1.5, 2.0, 3.0]
    }
    
    print("Pre-calculating Volatility...")
    from pricing.volatility import calc_rolling_hv
    df['rolling_hv'] = calc_rolling_hv(df['close'], window_days=30, periods_per_day=288)
    df['returns_1h'] = df['close'].pct_change(periods=12) # 5m * 12 = 1h
    df.bfill(inplace=True)
    
    optimizer = GridSearchOptimizer(base_config, valid_grid)
    
    import engine.optimizer
    original_run_single_backtest = engine.optimizer.run_single_backtest
    
    # Hack to auto-set MAX delta in worker based on MIN
    def worker_wrapper(params, df_split, base_conf):
        p = params.copy()
        p['TARGET_DELTA_MAX'] = p['TARGET_DELTA_MIN'] + 0.05
        return original_run_single_backtest(p, df_split, base_conf)
        
    engine.optimizer.run_single_backtest = worker_wrapper
    
    results = optimizer.optimize(df, train_split=0.7, n_jobs=-1)
    
    if not results.empty:
        generate_optimization_heatmap(results, 'TARGET_DELTA_MIN', 'SL_MULTIPLIER', 'Sharpe Ratio', 'heatmap_sharpe.html')
        generate_optimization_heatmap(results, 'TARGET_DELTA_MIN', 'SL_MULTIPLIER', 'Profit Factor', 'heatmap_pf.html')
        
if __name__ == "__main__":
    main()
