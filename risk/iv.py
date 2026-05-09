import pandas as pd
import numpy as np

def calc_rolling_hv(close_prices: pd.Series, window_days: int = 30, periods_per_day: int = 288) -> pd.Series:
    """
    Calculate annualized rolling historical volatility from a series of close prices.
    Assuming 5m data -> 288 periods per day.
    """
    window = window_days * periods_per_day
    log_returns = np.log(close_prices / close_prices.shift(1))
    rolling_std = log_returns.rolling(window=window).std()
    
    # 365 days for crypto
    return rolling_std * np.sqrt(365 * periods_per_day)

def get_dynamic_iv(spot: float, current_hv: float, short_term_returns: float, config: dict) -> dict:
    """
    Calculate skewed IVs based on realized volatility and nonlinear panic expansion.
    Returns: {'call': float, 'put': float}
    """
    base_iv = current_hv if current_hv and not np.isnan(current_hv) else config.get('CONSTANT_IV', 0.60)
    
    # Apply floor
    base_iv = max(base_iv, 0.30)
        
    # Nonlinear Panic Expansion
    # IV expands sharply if short term return is massive
    spike_threshold = config.get('IV_SPIKE_THRESHOLD_PCT', -0.02)
    panic_premium = 0.0
    if short_term_returns < spike_threshold:
        excess_drop = abs(short_term_returns) - abs(spike_threshold)
        # Quadratic expansion for panic
        panic_premium = config.get('IV_PANIC_MULT', 50.0) * (excess_drop ** 2)
        # Linear spike additive
        panic_premium += config.get('IV_SPIKE_MULT', 5.0) * excess_drop

    # Volatility Skew: OTM Puts usually trade higher IV than Calls
    skew_factor = config.get('PUT_SKEW_MULT', 1.15) # Puts are 15% more expensive base
    
    return {
        'call': base_iv + (panic_premium * 0.5), # Calls expand less in panic
        'put': (base_iv * skew_factor) + panic_premium
    }
