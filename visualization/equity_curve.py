import plotly.graph_objects as go
import pandas as pd
import numpy as np
from backtesting.portfolio import Portfolio
from config.settings import settings

def plot_equity(portfolio: Portfolio, filename: str = "equity_curve.html"):
    if not portfolio.equity_history:
        print("No equity history to plot.")
        return
        
    df = pd.DataFrame(portfolio.equity_history, columns=['timestamp', 'equity'])
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df['timestamp'], y=df['equity'], mode='lines', name='Equity'))
    fig.update_layout(title='Portfolio Equity Curve', xaxis_title='Time', yaxis_title='Equity ($)', template='plotly_dark')
    
    output_path = settings.RESEARCH_REPORTS_DIR / filename
    fig.write_html(str(output_path))
    print(f"Equity curve saved to {output_path}")
    
def generate_optimization_heatmap(results_df: pd.DataFrame, x_col: str, y_col: str, z_col: str, filename: str):
    """Generate a heatmap from optimization results."""
    # We need to aggregate z_col in case there are multiple matching x and y due to other parameters
    pivot = results_df.groupby([y_col, x_col])[z_col].mean().reset_index()
    pivot = pivot.pivot(index=y_col, columns=x_col, values=z_col)
    
    fig = go.Figure(data=go.Heatmap(
        z=pivot.values,
        x=pivot.columns,
        y=pivot.index,
        colorscale='Viridis'
    ))
    fig.update_layout(
        title=f'Optimization Heatmap: {z_col} by {x_col} & {y_col}',
        xaxis_title=x_col,
        yaxis_title=y_col,
        template='plotly_dark'
    )
    fig.write_html(filename)
    print(f"Generated heatmap: {filename}")
