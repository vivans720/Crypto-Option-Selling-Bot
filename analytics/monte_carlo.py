import pandas as pd
import numpy as np
from typing import List
import plotly.graph_objects as go

def run_monte_carlo(trades_pnl: List[float], start_capital: float, num_sims: int = 10000) -> dict:
    """
    Run Monte Carlo simulations by bootstrapping trade PnL sequences.
    """
    if not trades_pnl:
        return {}
        
    n_trades = len(trades_pnl)
    sim_results = []
    max_drawdowns = []
    
    all_equity_paths = []
    
    for _ in range(num_sims):
        # Sample with replacement
        sample_pnl = np.random.choice(trades_pnl, size=n_trades, replace=True)
        equity_path = start_capital + np.cumsum(sample_pnl)
        
        # Avoid negative equity in simulation context
        equity_path = np.maximum(equity_path, 0)
        
        sim_results.append(equity_path[-1])
        
        # Calculate max drawdown for this path
        rolling_max = np.maximum.accumulate(equity_path)
        # Handle zero rolling max to avoid division by zero
        drawdowns = np.where(rolling_max > 0, (equity_path - rolling_max) / rolling_max, 0)
        max_drawdowns.append(np.min(drawdowns))
        
        # Store a few paths for plotting
        if _ < 50:
            all_equity_paths.append(equity_path)
            
    sim_results = np.array(sim_results)
    max_drawdowns = np.array(max_drawdowns)
    
    # Ruin defined as hitting 50% drawdown
    ruin_count = np.sum(max_drawdowns <= -0.50)
    
    results = {
        'Final Equity Mean': np.mean(sim_results),
        'Final Equity Median': np.median(sim_results),
        'Final Equity 5th': np.percentile(sim_results, 5),
        'Final Equity 95th': np.percentile(sim_results, 95),
        'Max Drawdown Mean': np.mean(max_drawdowns),
        'Max Drawdown 95th': np.percentile(max_drawdowns, 5), # 5th percentile is worst drawdown
        'Probability of Ruin (50% DD)': ruin_count / num_sims,
        'Survival Probability': 1.0 - (ruin_count / num_sims),
        'paths': all_equity_paths
    }
    
    return results

def plot_monte_carlo(mc_results: dict, filename: str = "monte_carlo.html"):
    if not mc_results or 'paths' not in mc_results:
        return
        
    fig = go.Figure()
    
    # Plot paths
    for path in mc_results['paths']:
        fig.add_trace(go.Scatter(y=path, mode='lines', line=dict(width=1), opacity=0.3, showlegend=False))
        
    fig.update_layout(
        title=f"Monte Carlo Simulation (50 Paths) - Survival Prob: {mc_results['Survival Probability']:.2%}",
        xaxis_title="Trade Number",
        yaxis_title="Equity ($)",
        template="plotly_dark"
    )
    fig.write_html(filename)
