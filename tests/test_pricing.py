import pytest
from pricing.bs_model import calc_option_price, calc_greeks

def test_bs_pricing():
    S = 100.0
    K = 100.0
    T = 1.0
    r = 0.05
    sigma = 0.2
    
    # Expected values from standard BS calculators
    expected_call = 10.4506
    expected_put = 5.5735
    
    call_price = calc_option_price(S, K, T, r, sigma, 'call')
    put_price = calc_option_price(S, K, T, r, sigma, 'put')
    
    assert round(call_price, 4) == expected_call
    assert round(put_price, 4) == expected_put

def test_bs_greeks():
    S = 100.0
    K = 100.0
    T = 1.0
    r = 0.05
    sigma = 0.2
    
    call_greeks = calc_greeks(S, K, T, r, sigma, 'call')
    put_greeks = calc_greeks(S, K, T, r, sigma, 'put')
    
    # Call delta should be ~0.6368
    assert round(call_greeks['delta'], 4) == 0.6368
    
    # Put delta should be Call delta - 1
    assert round(put_greeks['delta'], 4) == round(0.6368 - 1, 4)
    
    # Gamma should be positive and same for both
    assert call_greeks['gamma'] > 0
    assert call_greeks['gamma'] == put_greeks['gamma']

def test_expired_options():
    # T = 0
    call_price = calc_option_price(105, 100, 0, 0.05, 0.2, 'call')
    put_price = calc_option_price(95, 100, 0, 0.05, 0.2, 'put')
    
    assert call_price == 5.0
    assert put_price == 5.0
