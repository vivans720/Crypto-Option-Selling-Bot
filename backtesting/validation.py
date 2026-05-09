import pandas as pd
from datetime import timedelta
from typing import List, Callable

def walk_forward_split(df: pd.DataFrame, train_days: int, test_days: int):
    """Generate train/test splits for walk-forward validation."""
    start_date = df['timestamp'].min()
    end_date = df['timestamp'].max()
    
    current_train_start = start_date
    while True:
        train_end = current_train_start + timedelta(days=train_days)
        test_end = train_end + timedelta(days=test_days)
        
        if test_end > end_date:
            break
            
        train_set = df[(df['timestamp'] >= current_train_start) & (df['timestamp'] < train_end)]
        test_set = df[(df['timestamp'] >= train_end) & (df['timestamp'] < test_end)]
        
        yield train_set, test_set
        
        # Advance by test_days (Rolling)
        current_train_start += timedelta(days=test_days)
