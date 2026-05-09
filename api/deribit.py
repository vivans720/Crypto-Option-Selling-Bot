import requests
import pandas as pd
from typing import Optional

BASE_URL = "https://www.deribit.com/api/v2/public"

def fetch_historical_volatility(currency: str, resolution: str, start_timestamp: str, end_timestamp: str) -> pd.DataFrame:
    """
    Fetch historical implied volatility from Deribit.
    Pure function, returns DataFrame. Throws RuntimeError on failure.
    """
    url = f"{BASE_URL}/get_historical_volatility"
    params = {
        "currency": currency,
        "resolution": resolution,
        "start_timestamp": start_timestamp,
        "end_timestamp": end_timestamp
    }
    
    response = requests.get(url, params=params)
    if response.status_code != 200:
        raise RuntimeError(f"Deribit API Error: {response.status_code} - {response.text}")
        
    data = response.json()
    if 'result' not in data or 'data' not in data['result']:
         raise RuntimeError("Unexpected API response format for volatility")
         
    records = data['result']['data']
    df = pd.DataFrame(records, columns=['timestamp', 'volatility'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    return df

def fetch_option_chain(currency: str, expiration_date: Optional[str] = None) -> pd.DataFrame:
    """
    Fetch current option chain for a currency and optional expiration.
    Extracts greeks into top-level columns.
    """
    url = f"{BASE_URL}/get_book_summary_by_currency"
    params = {
        "currency": currency,
        "kind": "option"
    }
    
    response = requests.get(url, params=params)
    if response.status_code != 200:
        raise RuntimeError(f"Deribit API Error: {response.status_code} - {response.text}")
        
    data = response.json()
    if 'result' not in data:
        raise RuntimeError("Unexpected API response format for option chain")
        
    instruments = data['result']
    if expiration_date:
        instruments = [inst for inst in instruments if expiration_date in inst.get('instrument_name', '')]
        
    parsed_data = []
    for inst in instruments:
        row = {
            'instrument_name': inst.get('instrument_name'),
            'strike': inst.get('strike'),
            'option_type': inst.get('option_type'), # Optional, might not exist in summary directly, usually parsed from instrument
            'mark_price': inst.get('mark_price'),
            'ask_price': inst.get('ask_price'),
            'bid_price': inst.get('bid_price'),
            'mark_iv': inst.get('mark_iv'),
        }
        
        # Parse option type from instrument name if not present
        if not row['option_type'] and row['instrument_name']:
            parts = row['instrument_name'].split('-')
            if len(parts) == 4:
                row['option_type'] = 'call' if parts[3] == 'C' else 'put'
                row['strike'] = float(parts[2])
                
        # Flatten Greeks
        greeks = inst.get('greeks', {})
        row['delta'] = greeks.get('delta') if greeks else None
        row['gamma'] = greeks.get('gamma') if greeks else None
        row['vega'] = greeks.get('vega') if greeks else None
        row['theta'] = greeks.get('theta') if greeks else None
            
        parsed_data.append(row)
        
    df = pd.DataFrame(parsed_data)
    return df
