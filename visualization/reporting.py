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
        rows=5, cols=1,
        shared_xaxes=False,
        vertical_spacing=0.05,
        subplot_titles=("Equity Curve", "Drawdown", "Daily Returns", "Trade Distribution", "Rolling Sharpe (30d)"),
        row_heights=[0.25, 0.15, 0.15, 0.25, 0.2]
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
    daily_ret = df_daily['equity'].pct_change().fillna(0)
    fig.add_trace(
        go.Bar(x=df_daily.index, y=daily_ret, name="Daily Returns", marker_color='grey'),
        row=3, col=1
    )
    
    # 4. Trade Distribution
    trades = [t.pnl for t in portfolio.trades if t.status == 'CLOSED']
    if trades:
        fig.add_trace(
            go.Histogram(x=trades, name="Trade PnL", marker_color='indigo', nbinsx=50),
            row=4, col=1
        )
        
    # 5. Rolling Sharpe
    rolling_std = daily_ret.rolling(30).std()
    rolling_sharpe = (daily_ret.rolling(30).mean() / rolling_std * np.sqrt(365)).fillna(0)
    # Replace inf with 0
    rolling_sharpe = rolling_sharpe.replace([np.inf, -np.inf], 0)
    
    fig.add_trace(
        go.Scatter(x=df_daily.index, y=rolling_sharpe, name="Rolling Sharpe (30d)", line=dict(color='orange')),
        row=5, col=1
    )
    
    fig.update_layout(
        height=1400,
        title_text="Strategy Performance Analytics",
        showlegend=False,
        template="plotly_dark"
    )
    
    html_path = reports_dir / "performance_dashboard.html"
    fig.write_html(str(html_path))
    print(f"Dashboard saved to {html_path}")

def plot_monthly_heatmap(equity_series: pd.Series, reports_dir: Path):
    """Generate monthly returns heatmap."""
    if equity_series.empty:
        return
        
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

def plot_yearly_stats(portfolio, reports_dir: Path):
    """Generate yearly stats table."""
    df_eq = pd.DataFrame(portfolio.equity_history, columns=['timestamp', 'equity']).set_index('timestamp')
    if df_eq.empty:
        return
        
    df_daily = df_eq.resample('1D').last().ffill()
    df_daily['year'] = df_daily.index.year
    
    yearly_returns = df_daily.groupby('year')['equity'].apply(lambda x: x.iloc[-1] / x.iloc[0] - 1)
    
    df_trades = pd.DataFrame([vars(t) for t in portfolio.trades if t.status == 'CLOSED'])
    
    if not df_trades.empty:
        df_trades['year'] = df_trades['entry_time'].dt.year
        yearly_trades = df_trades.groupby('year').size()
        yearly_winrate = df_trades.groupby('year').apply(lambda x: (x['pnl'] > 0).mean())
        yearly_pnl = df_trades.groupby('year')['pnl'].sum()
    else:
        yearly_trades = pd.Series(dtype=int)
        yearly_winrate = pd.Series(dtype=float)
        yearly_pnl = pd.Series(dtype=float)
        
    yearly_stats = pd.DataFrame({
        'Return': yearly_returns,
        'Trades': yearly_trades,
        'Win Rate': yearly_winrate,
        'Net PnL': yearly_pnl
    }).fillna(0)
    
    fig = go.Figure(data=[go.Table(
        header=dict(values=['Year', 'Return', 'Trades', 'Win Rate', 'Net PnL'],
                    fill_color='paleturquoise',
                    align='left'),
        cells=dict(values=[yearly_stats.index, 
                           np.round(yearly_stats['Return']*100, 2).astype(str) + '%', 
                           yearly_stats['Trades'], 
                           np.round(yearly_stats['Win Rate']*100, 2).astype(str) + '%', 
                           np.round(yearly_stats['Net PnL'], 2)],
                   fill_color='lavender',
                   align='left'))
    ])
    
    fig.update_layout(title="Yearly Performance Statistics")
    html_path = reports_dir / "yearly_stats.html"
    fig.write_html(str(html_path))

