import pandas as pd
import numpy as np
from typing import Dict, Optional
from risk.pricing import calculate_iv, calculate_greeks, delta, gamma, theta, vega, implied_volatility

def generate_synthetic_chain(spot: float, time_to_expiry_years: float, r: float, iv: float, num_strikes: int = 20, strike_interval: float = 500.0) -> pd.DataFrame:
    """
    Generate synthetic options chain (Calls and Puts) around the spot price.
    Returns DataFrame with strikes, prices, and Greeks.
    """
    if time_to_expiry_years <= 0:
        return pd.DataFrame()
        
    center_strike = round(spot / strike_interval) * strike_interval
    
    strikes = [center_strike + (i - num_strikes//2) * strike_interval for i in range(num_strikes)]
    
    from py_vollib.black_scholes import black_scholes
    
    data = []
    for K in strikes:
        if K <= 0:
            continue
            
        for opt_type in ['call', 'put']:
            flag = 'c' if opt_type == 'call' else 'p'
            price = black_scholes(flag, spot, K, time_to_expiry_years, r, iv)
            greeks = calculate_greeks(spot, K, time_to_expiry_years, r, iv, flag)
            
            data.append({
                'strike': K,
                'option_type': opt_type,
                'mark_price': price,
                'delta': greeks['delta'],
                'gamma': greeks['gamma'],
                'theta': greeks['theta'],
                'vega': greeks['vega']
            })
            
    return pd.DataFrame(data)

def select_strikes(chain_df: pd.DataFrame, target_delta_min: float, target_delta_max: float) -> Dict[str, Optional[dict]]:
    """
    Selects Call and Put options that match the target delta range.
    Returns a dict with 'call' and 'put' containing the row dict or None.
    """
    selected = {'call': None, 'put': None}
    
    if chain_df.empty:
        return selected
        
    calls = chain_df[chain_df['option_type'] == 'call'].copy()
    if not calls.empty:
        calls['delta_diff'] = calls['delta'].apply(
            lambda d: abs(d - ((target_delta_min + target_delta_max) / 2))
        )
        valid_calls = calls[(calls['delta'] >= target_delta_min) & (calls['delta'] <= target_delta_max)]
        if not valid_calls.empty:
            best_call = valid_calls.sort_values('delta_diff').iloc[0]
            selected['call'] = best_call.to_dict()

    puts = chain_df[chain_df['option_type'] == 'put'].copy()
    if not puts.empty:
        target_put_min = -target_delta_max
        target_put_max = -target_delta_min
        puts['delta_diff'] = puts['delta'].apply(
            lambda d: abs(d - ((target_put_min + target_put_max) / 2))
        )
        valid_puts = puts[(puts['delta'] >= target_put_min) & (puts['delta'] <= target_put_max)]
        if not valid_puts.empty:
            best_put = valid_puts.sort_values('delta_diff').iloc[0]
            selected['put'] = best_put.to_dict()
            
    return selected

def check_entry_conditions(current_time_hhmm: str, window_start: str, window_end: str) -> bool:
    return window_start <= current_time_hhmm <= window_end

def calculate_exit(position_state: dict, current_prices: dict, sl_multiplier: float) -> Optional[str]:
    if not position_state or not current_prices:
        return None
        
    call_entry = position_state.get('call_entry_price', 0)
    put_entry = position_state.get('put_entry_price', 0)
    
    call_current = current_prices.get('call_mark', 0)
    put_current = current_prices.get('put_mark', 0)
    
    combined_entry = call_entry + put_entry
    combined_current = call_current + put_current
    
    if combined_entry <= 0:
        return None
        
    combined_sl = combined_entry * sl_multiplier
    
    if combined_current >= combined_sl:
        return "COMBINED_SL_HIT"
        
    combined_tp = combined_entry * 0.05
    if combined_current <= combined_tp:
        return "COMBINED_TP_HIT"
        
    return None
