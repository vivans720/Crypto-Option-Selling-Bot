import pytest
from unittest.mock import patch, MagicMock
from api.deribit import fetch_historical_volatility, fetch_option_chain

@pytest.fixture
def mock_volatility_response():
    return {
        "result": {
            "data": [
                [1672531200000, 50.5],
                [1672617600000, 52.1]
            ]
        }
    }

@pytest.fixture
def mock_chain_response():
    return {
        "result": [
            {
                "instrument_name": "BTC-29DEC23-40000-C",
                "strike": 40000,
                "option_type": "call",
                "mark_price": 0.05,
                "ask_price": 0.052,
                "bid_price": 0.048,
                "mark_iv": 45.2,
                "greeks": {"delta": 0.45, "gamma": 0.001, "vega": 0.1, "theta": -0.05}
            },
            {
                "instrument_name": "BTC-29DEC23-40000-P",
                "strike": 40000,
                "option_type": "put",
                "mark_price": 0.04,
                "ask_price": 0.042,
                "bid_price": 0.038,
                "mark_iv": 46.1,
                "greeks": {"delta": -0.55, "gamma": 0.001, "vega": 0.1, "theta": -0.05}
            }
        ]
    }

@patch('requests.get')
def test_fetch_historical_volatility(mock_get, mock_volatility_response):
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = mock_volatility_response
    
    df = fetch_historical_volatility("BTC", "1", "1672531200000", "1672617600000")
    
    assert not df.empty
    assert 'volatility' in df.columns
    assert 'timestamp' in df.columns
    assert len(df) == 2
    assert df.iloc[0]['volatility'] == 50.5

@patch('requests.get')
def test_fetch_option_chain(mock_get, mock_chain_response):
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = mock_chain_response
    
    df = fetch_option_chain("BTC", "BTC-29DEC23")
    
    assert not df.empty
    assert len(df) == 2
    assert df.iloc[0]['instrument_name'] == "BTC-29DEC23-40000-C"
    assert df.iloc[0]['delta'] == 0.45
    assert df.iloc[1]['delta'] == -0.55

@patch('requests.get')
def test_fetch_historical_volatility_error(mock_get):
    mock_get.return_value.status_code = 500
    
    with pytest.raises(RuntimeError):
        fetch_historical_volatility("BTC", "1", "1672531200000", "1672617600000")
