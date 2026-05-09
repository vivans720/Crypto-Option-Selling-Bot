import numpy as np
from scipy.stats import norm

def d1(S: float, K: float, T: float, r: float, sigma: float) -> float:
    """Calculate d1 for Black-Scholes."""
    if T <= 0 or sigma <= 0 or K <= 0 or S <= 0:
        return 0.0
    return (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))

def d2(d1_val: float, T: float, sigma: float) -> float:
    """Calculate d2 for Black-Scholes."""
    if T <= 0 or sigma <= 0:
        return 0.0
    return d1_val - sigma * np.sqrt(T)

def calc_option_price(S: float, K: float, T: float, r: float, sigma: float, option_type: str) -> float:
    """
    Calculate theoretical option price using Black-Scholes.
    S: Spot price
    K: Strike price
    T: Time to maturity (in years)
    r: Risk-free rate (annualized)
    sigma: Volatility (annualized)
    option_type: 'call' or 'put'
    """
    if T <= 0:
        return max(0.0, S - K) if option_type == 'call' else max(0.0, K - S)
        
    d1_val = d1(S, K, T, r, sigma)
    d2_val = d2(d1_val, T, sigma)
    
    if option_type == 'call':
        return S * norm.cdf(d1_val) - K * np.exp(-r * T) * norm.cdf(d2_val)
    elif option_type == 'put':
        return K * np.exp(-r * T) * norm.cdf(-d2_val) - S * norm.cdf(-d1_val)
    else:
        raise ValueError("option_type must be 'call' or 'put'")

def calc_greeks(S: float, K: float, T: float, r: float, sigma: float, option_type: str) -> dict:
    """
    Calculate Greeks (Delta, Gamma, Theta, Vega) using Black-Scholes.
    """
    if T <= 0:
        return {
            'delta': 1.0 if option_type == 'call' and S > K else (-1.0 if option_type == 'put' and K > S else 0.0),
            'gamma': 0.0,
            'theta': 0.0,
            'vega': 0.0
        }
        
    d1_val = d1(S, K, T, r, sigma)
    d2_val = d2(d1_val, T, sigma)
    
    # Delta
    if option_type == 'call':
        delta = norm.cdf(d1_val)
    else:
        delta = norm.cdf(d1_val) - 1.0
        
    # Gamma (same for call and put)
    gamma = norm.pdf(d1_val) / (S * sigma * np.sqrt(T))
    
    # Vega (same for call and put, usually expressed per 1% change, but returning absolute here)
    vega = S * norm.pdf(d1_val) * np.sqrt(T) / 100.0 # Standard convention / 100
    
    # Theta (usually expressed per day)
    term1 = -(S * norm.pdf(d1_val) * sigma) / (2 * np.sqrt(T))
    if option_type == 'call':
        theta = term1 - r * K * np.exp(-r * T) * norm.cdf(d2_val)
    else:
        theta = term1 + r * K * np.exp(-r * T) * norm.cdf(-d2_val)
    theta = theta / 365.0 # Per day
    
    return {
        'delta': delta,
        'gamma': gamma,
        'theta': theta,
        'vega': vega
    }
