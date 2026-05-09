import pandas as pd
import numpy as np
import itertools
from joblib import Parallel, delayed
from tqdm import tqdm
import os
from engine.backtest import BacktestEngine
from analytics.metrics import generate_summary

def run_single_backtest(params: dict, df: pd.DataFrame, base_config: dict) -> dict:
    """Worker function to run a single backtest for a parameter combination."""
    config = base_config.copy()
    config.update(params)
    
    engine = BacktestEngine(config)
    engine.run(df)
    
    # Force close any open trades at the end of the split
    open_trades = engine.portfolio.get_open_trades()
    for t in open_trades:
        last_spot = df.iloc[-1]['close']
        last_ts = df.iloc[-1]['timestamp']
        from pricing.bs_model import calc_option_price
        c_mark = calc_option_price(last_spot, t.call_strike, 1.0/365.0, config['RISK_FREE_RATE'], config.get('CONSTANT_IV', 0.60), 'call')
        p_mark = calc_option_price(last_spot, t.put_strike, 1.0/365.0, config['RISK_FREE_RATE'], config.get('CONSTANT_IV', 0.60), 'put')
        t.close(last_ts, c_mark, p_mark, "END_OF_BACKTEST", config['FEES_PERCENT'])
        
    summary = generate_summary(engine.portfolio)
    
    # Flatten params into summary
    result = {**params, **summary}
    return result, engine.portfolio.trades

class GridSearchOptimizer:
    def __init__(self, base_config: dict, param_grid: dict):
        self.base_config = base_config
        self.param_grid = param_grid
        self.results_file = "optimization_results.parquet"
        
    def optimize(self, df: pd.DataFrame, train_split: float = 0.7, n_jobs: int = -1):
        # Split data
        split_idx = int(len(df) * train_split)
        train_df = df.iloc[:split_idx].copy()
        val_df = df.iloc[split_idx:].copy()
        
        print(f"Data Split -> Train: {len(train_df)} rows, Validation: {len(val_df)} rows.")
        
        # Generate grid
        keys, values = zip(*self.param_grid.items())
        combinations = [dict(zip(keys, v)) for v in itertools.product(*values)]
        print(f"Total Parameter Combinations: {len(combinations)}")
        
        # Check Resume
        existing_results = pd.DataFrame()
        if os.path.exists(self.results_file):
            existing_results = pd.read_parquet(self.results_file)
            print(f"Loaded {len(existing_results)} previous results from {self.results_file}")
            
            # Filter combinations already completed
            # To do this safely, we convert dicts to string tuples for comparison
            if not existing_results.empty:
                completed_sets = set(
                    tuple(row[k] for k in keys) for _, row in existing_results.iterrows()
                )
                combinations = [c for c in combinations if tuple(c[k] for k in keys) not in completed_sets]
                print(f"Remaining combinations to process: {len(combinations)}")
        
        if not combinations:
            print("Optimization already fully complete.")
            return existing_results
            
        # Run Parallel
        print("Running Optimization on Train Set...")
        
        # We process in chunks to save progress periodically
        chunk_size = 100
        all_results_df = existing_results
        
        best_trades = None
        best_sharpe = -999.0
        
        for i in range(0, len(combinations), chunk_size):
            chunk = combinations[i:i+chunk_size]
            
            # Execute chunk
            chunk_results = Parallel(n_jobs=n_jobs)(
                delayed(run_single_backtest)(params, train_df, self.base_config) for params in tqdm(chunk, desc=f"Chunk {i//chunk_size + 1}")
            )
            
            # Extract results and identify if we got a new best trades
            chunk_dicts = []
            for res_dict, trades in chunk_results:
                chunk_dicts.append(res_dict)
                if res_dict['Sharpe Ratio'] > best_sharpe:
                    best_sharpe = res_dict['Sharpe Ratio']
                    best_trades = trades
            
            # Save progress
            df_chunk = pd.DataFrame(chunk_dicts)
            all_results_df = pd.concat([all_results_df, df_chunk], ignore_index=True)
            all_results_df.to_parquet(self.results_file, index=False)
            
            current_best = all_results_df.sort_values(by='Sharpe Ratio', ascending=False).iloc[0]
            print(f"Progress Saved. Current Best Sharpe: {current_best['Sharpe Ratio']:.2f} | PF: {current_best['Profit Factor']:.2f}")
            
        print("Optimization Complete!")
        
        # Rank by Sharpe
        ranked = all_results_df.sort_values(by=['Sharpe Ratio', 'Profit Factor'], ascending=[False, False])
        ranked.to_parquet(self.results_file, index=False)
        ranked.to_csv("optimization_results.csv", index=False) # Human readable backup
        
        if best_trades:
            df_trades = pd.DataFrame([vars(t) for t in best_trades])
            df_trades.to_parquet("best_strategy_trades.parquet", index=False)
            print("Saved best_strategy_trades.parquet")
            
        # Run Walk-Forward on Best Configuration
        best_params = {k: ranked.iloc[0][k] for k in keys}
        print("\nRunning Walk-Forward Validation on Best Parameters:")
        print(best_params)
        
        val_res, _ = run_single_backtest(best_params, val_df, self.base_config)
        print("--- Validation Results ---")
        for k, v in val_res.items():
            if k not in keys:
                print(f"{k}: {v}")
                
        return ranked
