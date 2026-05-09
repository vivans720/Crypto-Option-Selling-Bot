import pandas as pd
import numpy as np

def calc_rolling_hv(close_prices: pd.Series, window_days: int = 30, periods_per_day: int = 288) -> pd.Series:
    """Annualized rolling historical volatility."""
    window = window_days * periods_per_day
    log_returns = np.log(close_prices / close_prices.shift(1))
    return log_returns.rolling(window=window).std() * np.sqrt(365 * periods_per_day)

def calculate_iv_rank(current_iv: float, iv_history: pd.Series) -> float:
    """IV Rank = (Current - Min) / (Max - Min)"""
    if iv_history.empty: return 0.5
    iv_min = iv_history.min()
    iv_max = iv_history.max()
    if iv_max == iv_min: return 0.5
    return (current_iv - iv_min) / (iv_max - iv_min)

def calculate_iv_percentile(current_iv: float, iv_history: pd.Series) -> float:
    """IV Percentile = % of days IV was lower than current."""
    if iv_history.empty: return 0.5
    return (iv_history < current_iv).mean()

def get_dynamic_iv(spot: float, current_hv: float, short_term_returns: float, config: dict) -> dict:
    """Skewed IVs based on realized volatility and panic."""
    base_iv = current_hv if current_hv and not np.isnan(current_hv) else config.get('CONSTANT_IV', 0.60)
    base_iv = max(base_iv, 0.30)
        
    spike_threshold = config.get('IV_SPIKE_THRESHOLD_PCT', -0.02)
    panic_premium = 0.0
    if short_term_returns < spike_threshold:
        excess_drop = abs(short_term_returns) - abs(spike_threshold)
        panic_premium = config.get('IV_PANIC_MULT', 50.0) * (excess_drop ** 2)
        panic_premium += config.get('IV_SPIKE_MULT', 5.0) * excess_drop

    skew_factor = config.get('PUT_SKEW_MULT', 1.15)
    
    return {
        'call': base_iv + (panic_premium * 0.5),
        'put': (base_iv * skew_factor) + panic_premium
    }
