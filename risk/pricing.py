from py_vollib.black_scholes.implied_volatility import implied_volatility
from py_vollib.black_scholes.greeks.analytical import delta, gamma, theta, vega

def calculate_iv(price, S, K, t, r, flag):
    """
    Calculate implied volatility using py_vollib.
    flag: 'c' for call, 'p' for put
    """
    try:
        return implied_volatility(price, S, K, t, r, flag)
    except:
        return 0.0

def calculate_greeks(S, K, t, r, sigma, flag):
    """
    Calculate Greeks using py_vollib.
    """
    try:
        res = {
            'delta': delta(flag, S, K, t, r, sigma),
            'gamma': gamma(flag, S, K, t, r, sigma),
            'theta': theta(flag, S, K, t, r, sigma),
            'vega': vega(flag, S, K, t, r, sigma)
        }
        return res
    except:
        return {'delta': 0, 'gamma': 0, 'theta': 0, 'vega': 0}
