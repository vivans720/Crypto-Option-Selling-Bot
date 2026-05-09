import pytest
from datetime import datetime
from engine.portfolio import Portfolio, Trade
from analytics.metrics import calc_pnl, calc_win_rate, calc_max_drawdown, generate_summary

@pytest.fixture
def sample_portfolio():
    p = Portfolio(1000)
    
    t1 = Trade("1", datetime.now(), 100, 100, 40000, 30000, 1.0)
    t1.pnl = 50
    t1.status = "CLOSED"
    
    t2 = Trade("2", datetime.now(), 100, 100, 40000, 30000, 1.0)
    t2.pnl = -20
    t2.status = "CLOSED"
    
    p.add_trade(t1)
    p.add_trade(t2)
    
    p.equity_curve = [
        {'timestamp': datetime(2023,1,1), 'equity': 1000},
        {'timestamp': datetime(2023,1,2), 'equity': 1050},
        {'timestamp': datetime(2023,1,3), 'equity': 1030}
    ]
    return p

def test_metrics(sample_portfolio):
    assert calc_pnl(sample_portfolio) == 30
    assert calc_win_rate(sample_portfolio) == 0.5
    
    # max drawdown: peak 1050, drops to 1030. DD = -20/1050 = -0.01904...
    dd = calc_max_drawdown(sample_portfolio)
    assert round(dd, 4) == -0.0190
    
    summary = generate_summary(sample_portfolio)
    assert summary["Net PnL"] == 30
    assert summary["Total Trades"] == 2
