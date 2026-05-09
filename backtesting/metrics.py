import pandas as pd
import numpy as np
from backtesting.portfolio import Portfolio
from typing import Dict, Any

def calculate_max_drawdown(equity_series: pd.Series) -> float:
    if equity_series.empty:
        return 0.0
    rolling_max = equity_series.cummax()
    drawdowns = (equity_series - rolling_max) / rolling_max
    return drawdowns.min()

def calculate_sortino_ratio(returns: pd.Series, rf: float = 0.0, periods: int = 365) -> float:
    """Calculate Sortino Ratio (downside risk only)."""
    if returns.empty or returns.std() == 0:
        return 0.0
    expected_return = returns.mean() * periods
    downside_returns = returns[returns < 0]
    downside_std = downside_returns.std() * np.sqrt(periods)
    if downside_std == 0:
        return 0.0
    return (expected_return - rf) / downside_std

def calculate_calmar_ratio(annual_return: float, max_dd: float) -> float:
    """Calculate Calmar Ratio."""
    if max_dd == 0:
        return 0.0
    return annual_return / abs(max_dd)

def generate_summary(portfolio: Portfolio) -> dict:
    trades = [t for t in portfolio.trades if t.status == 'CLOSED']
    
    if not trades:
        return {'Status': 'No Closed Trades'}
        
    pnl_list = [t.pnl for t in trades]
    wins = [p for p in pnl_list if p > 0]
    losses = [p for p in pnl_list if p <= 0]
    
    win_rate = len(wins) / len(trades)
    net_pnl = sum(pnl_list)
    
    gross_profit = sum(wins) if wins else 0.0
    gross_loss = abs(sum(losses)) if losses else 0.0
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
    
    avg_win = np.mean(wins) if wins else 0.0
    avg_loss = np.mean(losses) if losses else 0.0
    
    expectancy = (win_rate * avg_win) + ((1 - win_rate) * avg_loss)
    
    streak = 0
    max_losing_streak = 0
    for p in pnl_list:
        if p <= 0:
            streak += 1
            max_losing_streak = max(max_losing_streak, streak)
        else:
            streak = 0
    
    df_eq = pd.DataFrame(portfolio.equity_history, columns=['timestamp', 'equity']).set_index('timestamp')
    df_daily = df_eq.resample('1D').last().ffill()
    daily_returns = df_daily['equity'].pct_change().dropna()
    
    total_days = (df_daily.index[-1] - df_daily.index[0]).days if len(df_daily) > 1 else 1
    annual_return = (portfolio.current_equity / portfolio.capital - 1) * (365 / max(total_days, 1))
    
    max_dd = calculate_max_drawdown(df_daily['equity'])
    sharpe = (daily_returns.mean() / daily_returns.std() * np.sqrt(365)) if daily_returns.std() > 0 else 0
    sortino = calculate_sortino_ratio(daily_returns)
    calmar = calculate_calmar_ratio(annual_return, max_dd)
    
    # Trade Level Analytics
    trade_pnls = pd.Series(pnl_list)
    
    return {
        'Total Trades': len(trades),
        'Win Rate': win_rate,
        'Net PnL': net_pnl,
        'Profit Factor': profit_factor,
        'Expectancy': expectancy,
        'Max Drawdown': max_dd,
        'Sharpe Ratio': sharpe,
        'Sortino Ratio': sortino,
        'Calmar Ratio': calmar,
        'Annual Return': annual_return,
        'Largest Win': trade_pnls.max(),
        'Largest Loss': trade_pnls.min(),
        'Avg Win': avg_win,
        'Avg Loss': avg_loss,
        'Avg Profit': trade_pnls.mean(),
        'Longest Losing Streak': max_losing_streak,
        'Recovery Factor': net_pnl / abs(max_dd * portfolio.capital) if max_dd != 0 else 0
    }
