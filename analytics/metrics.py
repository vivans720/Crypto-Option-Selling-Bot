import pandas as pd
import numpy as np
from engine.portfolio import Portfolio

def calculate_max_drawdown(equity_series: pd.Series) -> float:
    if equity_series.empty:
        return 0.0
    rolling_max = equity_series.cummax()
    drawdowns = (equity_series - rolling_max) / rolling_max
    return drawdowns.min()

def generate_summary(portfolio: Portfolio) -> dict:
    trades = [t for t in portfolio.trades if t.status == 'CLOSED']
    
    if not trades:
        return {
            'Total Trades': 0,
            'Net PnL': 0.0,
            'Win Rate': 0.0,
            'Max Drawdown': 0.0,
            'Final Equity': portfolio.current_equity,
            'Sharpe Ratio': 0.0,
            'Profit Factor': 0.0,
            'Largest Loss': 0.0,
            'Expectancy': 0.0
        }
        
    pnl_list = [t.pnl for t in trades]
    wins = [p for p in pnl_list if p > 0]
    losses = [p for p in pnl_list if p <= 0]
    
    win_rate = len(wins) / len(trades)
    net_pnl = sum(pnl_list)
    
    gross_profit = sum(wins) if wins else 0.0
    gross_loss = abs(sum(losses)) if losses else 0.0
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
    
    largest_loss = min(losses) if losses else 0.0
    avg_win = np.mean(wins) if wins else 0.0
    avg_loss = np.mean(losses) if losses else 0.0
    expectancy = (win_rate * avg_win) + ((1 - win_rate) * avg_loss)
    
    if portfolio.equity_history:
        df_eq = pd.DataFrame(portfolio.equity_history, columns=['timestamp', 'equity']).set_index('timestamp')
        max_dd = calculate_max_drawdown(df_eq['equity'])
        
        # Calculate daily returns
        df_daily = df_eq.resample('1D').last().ffill()
        daily_returns = df_daily['equity'].pct_change().dropna()
        
        # Rolling Metrics
        rolling_sharpe = daily_returns.rolling(window=30).mean() / daily_returns.rolling(window=30).std() * np.sqrt(365)
        
        # Monthly/Yearly Returns
        monthly_returns = df_daily['equity'].resample('ME').last().pct_change().dropna()
        yearly_returns = df_daily['equity'].resample('YE').last().pct_change().dropna()
        
        if len(daily_returns) > 1 and daily_returns.std() > 0:
            sharpe_ratio = np.sqrt(365) * (daily_returns.mean() / daily_returns.std())
        else:
            sharpe_ratio = 0.0
            
        worst_trade = min(pnl_list) if pnl_list else 0.0
    else:
        max_dd = 0.0
        sharpe_ratio = 0.0
        worst_trade = 0.0
        monthly_returns = pd.Series()
        yearly_returns = pd.Series()
        
    return {
        'Total Trades': len(trades),
        'Net PnL': net_pnl,
        'Win Rate': win_rate,
        'Max Drawdown': max_dd,
        'Final Equity': portfolio.current_equity,
        'Sharpe Ratio': sharpe_ratio,
        'Profit Factor': profit_factor,
        'Largest Loss': largest_loss,
        'Expectancy': expectancy,
        'Worst Trade': worst_trade,
        'Monthly Returns': monthly_returns.to_dict(),
        'Yearly Returns': yearly_returns.to_dict()
    }
