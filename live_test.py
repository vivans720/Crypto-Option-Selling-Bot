import pandas as pd
from datetime import datetime
import config.settings as settings
from api.deribit import fetch_option_chain
from strategy.core import select_strikes

def test_live_chain():
    print("Fetching live BTC option chain from Deribit...")
    try:
        # Fetch live chain
        df_chain = fetch_option_chain("BTC")
        print(f"Fetched {len(df_chain)} option instruments.")
        
        # Select strikes based on target delta
        print(f"Selecting strikes for Delta {settings.TARGET_DELTA_MIN} - {settings.TARGET_DELTA_MAX}...")
        strikes = select_strikes(df_chain, settings.TARGET_DELTA_MIN, settings.TARGET_DELTA_MAX)
        
        if strikes['call']:
            c = strikes['call']
            print(f"Call Selected: {c['instrument_name']} | Delta: {c['delta']} | Mark: {c['mark_price']}")
        else:
            print("No Call found matching delta criteria.")
            
        if strikes['put']:
            p = strikes['put']
            print(f"Put Selected: {p['instrument_name']} | Delta: {p['delta']} | Mark: {p['mark_price']}")
        else:
            print("No Put found matching delta criteria.")
            
    except Exception as e:
        print(f"Error fetching live data: {e}")

if __name__ == "__main__":
    test_live_chain()
