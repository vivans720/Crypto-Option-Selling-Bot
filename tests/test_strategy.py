import pytest
import pandas as pd
from strategy.core import generate_synthetic_chain, select_strikes, calculate_exit

def test_generate_synthetic_chain():
    spot = 40000
    T = 1.0 / 365.0  # 1 day to expiry
    r = 0.05
    iv = 0.60
    
    df = generate_synthetic_chain(spot, T, r, iv, num_strikes=10, strike_interval=500.0)
    
    assert not df.empty
    assert 'mark_price' in df.columns
    assert 'delta' in df.columns
    assert len(df) == 20  # 10 strikes * 2 option types
    
    # Check calls have positive delta, puts have negative delta
    assert (df[df['option_type'] == 'call']['delta'] >= 0).all()
    assert (df[df['option_type'] == 'put']['delta'] <= 0).all()

def test_select_strikes_synthetic():
    spot = 40000
    T = 1.0 / 365.0
    r = 0.05
    iv = 0.60
    
    # Large chain to ensure we have a delta between 0.1 and 0.15
    df = generate_synthetic_chain(spot, T, r, iv, num_strikes=60, strike_interval=500.0)
    
    selected = select_strikes(df, 0.10, 0.15)
    
    assert selected['call'] is not None
    assert 0.10 <= selected['call']['delta'] <= 0.15
    
    assert selected['put'] is not None
    assert -0.15 <= selected['put']['delta'] <= -0.10

def test_calculate_exit():
    pos = {'call_entry_price': 100, 'put_entry_price': 100}
    assert calculate_exit(pos, {'call_mark': 90, 'put_mark': 90}, 2.0) is None
    assert calculate_exit(pos, {'call_mark': 250, 'put_mark': 160}, 2.0) == "COMBINED_SL_HIT"
