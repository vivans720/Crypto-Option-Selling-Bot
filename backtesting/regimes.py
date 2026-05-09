import pandas as pd
import numpy as np
from backtesting.portfolio import Portfolio

def classify_regimes(ohlcv_df: pd.DataFrame, portfolio: Portfolio) -> pd.DataFrame:
    """Classifies trades into market regimes based on the state of the market at entry time."""
    if not portfolio.trades or ohlcv_df.empty:
        return pd.DataFrame()
        
    df = ohlcv_df.copy()
    if 'timestamp' in df.columns:
        df.set_index('timestamp', inplace=True)
    
    # Simple proxy for trend: 7-day moving average (assuming 5m timeframe: 12 * 24 * 7 = 2016)
    sma_period = 2016 if len(df) > 3000 else 200
    df['sma'] = df['close'].rolling(sma_period).mean()
    
    if 'rolling_hv' not in df.columns:
        df['rolling_hv'] = df['close'].pct_change().rolling(288).std() * np.sqrt(288 * 365)
        
    median_hv = df['rolling_hv'].median()
    
    df['trend'] = np.where(df['close'] > df['sma'] * 1.02, 'Bull', 
                           np.where(df['close'] < df['sma'] * 0.98, 'Bear', 'Sideways'))
                           
    df['vol_regime'] = np.where(df['rolling_hv'] > median_hv * 1.2, 'High Vol',
                                np.where(df['rolling_hv'] < median_hv * 0.8, 'Low Vol', 'Normal Vol'))
                                
    trade_data = []
    capital = portfolio.capital
    
    for t in portfolio.trades:
        if t.status != 'CLOSED':
            continue
            
        try:
            entry_idx = df.index.get_indexer([t.entry_time], method='nearest')[0]
            if entry_idx >= 0:
                row = df.iloc[entry_idx]
                trade_data.append({
                    'trade_id': t.id,
                    'pnl': t.pnl,
                    'trend': row['trend'],
                    'vol_regime': row['vol_regime']
                })
        except KeyError:
            continue
            
    res_df = pd.DataFrame(trade_data)
    if not res_df.empty:
        # Calculate drawdown per regime
        res_df['cumulative_pnl'] = res_df.groupby('trend')['pnl'].cumsum()
        res_df['rolling_max'] = res_df.groupby('trend')['cumulative_pnl'].cummax()
        res_df['drawdown'] = np.where(
            res_df['rolling_max'] > 0,
            (res_df['cumulative_pnl'] - res_df['rolling_max']) / (capital + res_df['rolling_max']),
            res_df['cumulative_pnl'] / capital
        )
        # Fix missing values
        res_df['drawdown'] = res_df['drawdown'].fillna(0)
        
    return res_df
