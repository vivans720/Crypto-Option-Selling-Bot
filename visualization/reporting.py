import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from pathlib import Path
from config.settings import settings

def plot_performance_dashboard(portfolio, reports_dir: Path):
    """Generate professional Plotly dashboard."""
    reports_dir.mkdir(parents=True, exist_ok=True)
    
    df_eq = pd.DataFrame(portfolio.equity_history, columns=['timestamp', 'equity']).set_index('timestamp')
    df_daily = df_eq.resample('1D').last().ffill()
    
    # Create Subplots
    fig = make_subplots(
        rows=3, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.05,
        subplot_titles=("Equity Curve", "Drawdown", "Daily Returns"),
        row_heights=[0.5, 0.25, 0.25]
    )
    
    # 1. Equity Curve
    fig.add_trace(
        go.Scatter(x=df_eq.index, y=df_eq['equity'], name="Equity", line=dict(color='royalblue', width=2)),
        row=1, col=1
    )
    
    # 2. Drawdown
    rolling_max = df_daily['equity'].cummax()
    drawdown = (df_daily['equity'] - rolling_max) / rolling_max
    fig.add_trace(
        go.Scatter(x=df_daily.index, y=drawdown, name="Drawdown", fill='tozeroy', line=dict(color='crimson')),
        row=2, col=1
    )
    
    # 3. Returns
    daily_ret = df_daily['equity'].pct_change()
    fig.add_trace(
        go.Bar(x=df_daily.index, y=daily_ret, name="Daily Returns", marker_color='grey'),
        row=3, col=1
    )
    
    fig.update_layout(
        height=1000,
        title_text="Strategy Performance Analytics",
        showlegend=False,
        template="plotly_dark"
    )
    
    html_path = reports_dir / "performance_dashboard.html"
    fig.write_html(str(html_path))
    print(f"Dashboard saved to {html_path}")

def plot_monthly_heatmap(equity_series: pd.Series, reports_dir: Path):
    """Generate monthly returns heatmap."""
    monthly_ret = equity_series.resample('ME').last().pct_change()
    df_heat = monthly_ret.to_frame('returns')
    df_heat['year'] = df_heat.index.year
    df_heat['month'] = df_heat.index.month
    
    pivot = df_heat.pivot(index='year', columns='month', values='returns')
    
    fig = go.Figure(data=go.Heatmap(
        z=pivot.values,
        x=[f"Month {m}" for m in pivot.columns],
        y=pivot.index,
        colorscale='RdYlGn',
        text=np.round(pivot.values * 100, 2),
        texttemplate="%{text}%"
    ))
    
    fig.update_layout(title="Monthly Returns Heatmap", template="plotly_dark")
    
    html_path = reports_dir / "monthly_heatmap.html"
    fig.write_html(str(html_path))
