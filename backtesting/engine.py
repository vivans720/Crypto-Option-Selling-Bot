import pandas as pd
import numpy as np
import uuid
from typing import Dict, Any
from datetime import datetime, UTC
from backtesting.portfolio import Portfolio, Trade
from backtesting.models import ExecutionConfig, calculate_slippage, check_liquidation
from strategies.base import generate_synthetic_chain, select_strikes, calculate_exit
from risk.iv import get_dynamic_iv, calc_rolling_hv
from py_vollib.black_scholes import black_scholes

def _get_t_years(current_ts: datetime, exit_time_str: str) -> float:
    exit_hour, exit_minute = map(int, exit_time_str.split(':'))
    expiry_dt = current_ts.replace(hour=exit_hour, minute=exit_minute, second=0, microsecond=0)
    if current_ts >= expiry_dt:
        return 0.0
    return (expiry_dt - current_ts).total_seconds() / (365.0 * 24.0 * 3600.0)

class BacktestEngine:
    def __init__(self, config: Dict[str, Any], exec_config: ExecutionConfig = ExecutionConfig()):
        self.config = config
        self.exec_config = exec_config
        self.portfolio = Portfolio(config.get('START_CAPITAL', 10000.0))
        
    def _precompute_indicators(self, df: pd.DataFrame):
        """Vectorized pre-computation of indicators."""
        df['rolling_hv'] = calc_rolling_hv(df['close'], window_days=30, periods_per_day=288)
        df['returns_1h'] = df['close'].pct_change(periods=12)
        df['candle_move'] = (df['close'] - df['open']).abs() / df['open']
        df['vol_ratio'] = df['candle_move'] / df['candle_move'].rolling(100).mean().replace(0, 1e-9)
        df.bfill(inplace=True)
        return df

    def run(self, ohlcv_df: pd.DataFrame):
        r = self.config.get('RISK_FREE_RATE', 0.05)
        exit_time_str = self.config.get('EXIT_TIME', '23:55')
        
        ohlcv_df = self._precompute_indicators(ohlcv_df)
        
        for row in ohlcv_df.itertuples():
            spot = row.close
            timestamp = row.timestamp
            time_str = timestamp.strftime("%H:%M")
            
            # Volatility-adjusted slippage
            current_slippage = calculate_slippage(
                self.exec_config.fixed_slippage, 
                row.vol_ratio, 
                self.exec_config
            )
            
            T_YEARS = _get_t_years(timestamp, exit_time_str)
            iv_dict = get_dynamic_iv(spot, row.rolling_hv, row.returns_1h, self.config)
            
            open_trades = self.portfolio.get_open_trades()
            
            # 1. Manage Exits
            for trade in open_trades:
                c_mark = black_scholes('c', spot, trade.call_strike, T_YEARS, r, iv_dict['call'])
                p_mark = black_scholes('p', spot, trade.put_strike, T_YEARS, r, iv_dict['put'])
                
                current_prices = {'call_mark': c_mark, 'put_mark': p_mark}
                pos_state = {'call_entry_price': trade.entry_price_call, 'put_entry_price': trade.entry_price_put}
                
                exit_reason = calculate_exit(pos_state, current_prices, self.config.get('SL_MULTIPLIER', 2.0))
                
                if not exit_reason and (time_str >= exit_time_str or T_YEARS <= 0):
                    exit_reason = "EXPIRY"
                
                # Check for liquidation
                # Simplified margin: 10% of notional
                margin_used = spot * 0.1 * trade.qty 
                if not exit_reason and check_liquidation(self.portfolio.current_equity, margin_used, self.exec_config):
                    exit_reason = "LIQUIDATED"

                if exit_reason:
                    # Taker fee for exit
                    fee_pct = self.exec_config.taker_fee
                    # Worse slippage for SL/Liquidations
                    mult = 2.0 if exit_reason in ["COMBINED_SL_HIT", "LIQUIDATED"] else 1.0
                    
                    c_exit = c_mark * (1 + (current_slippage * mult))
                    p_exit = p_mark * (1 + (current_slippage * mult))
                    
                    trade.close(
                        exit_time=timestamp,
                        exit_call=c_exit,
                        exit_put=p_exit,
                        reason=exit_reason,
                        fees_percent=fee_pct
                    )
            
            # 2. Manage Entries
            if not self.portfolio.get_open_trades():
                if self.config.get('ENTRY_WINDOW_START', '07:00') <= time_str <= self.config.get('ENTRY_WINDOW_END', '09:00'):
                    last_closed = [t for t in self.portfolio.trades if t.status == 'CLOSED']
                    already_traded_today = False
                    if last_closed:
                        if last_closed[-1].entry_time.date() == timestamp.date():
                            already_traded_today = True
                            
                    if not already_traded_today and T_YEARS > 0:
                        avg_iv = (iv_dict['call'] + iv_dict['put']) / 2
                        chain = generate_synthetic_chain(spot, T_YEARS, r, avg_iv)
                        strikes = select_strikes(
                            chain, 
                            self.config.get('TARGET_DELTA_MIN', 0.10),
                            self.config.get('TARGET_DELTA_MAX', 0.15)
                        )
                        
                        if strikes['call'] and strikes['put']:
                            c_exec_mark = black_scholes('c', spot, strikes['call']['strike'], T_YEARS, r, iv_dict['call'])
                            p_exec_mark = black_scholes('p', spot, strikes['put']['strike'], T_YEARS, r, iv_dict['put'])
                            
                            # Maker fee for entry
                            c_entry = c_exec_mark * (1 - current_slippage)
                            p_entry = p_exec_mark * (1 - current_slippage)
                            
                            new_trade = Trade(
                                id=str(uuid.uuid4()),
                                entry_time=timestamp,
                                entry_price_call=c_entry,
                                entry_price_put=p_entry,
                                call_strike=strikes['call']['strike'],
                                put_strike=strikes['put']['strike'],
                                qty=1.0 
                            )
                            self.portfolio.add_trade(new_trade)
            
            # 3. Record Equity
            open_pnl = 0.0
            for t in self.portfolio.get_open_trades():
                c_mark = black_scholes('c', spot, t.call_strike, T_YEARS, r, iv_dict['call'])
                p_mark = black_scholes('p', spot, t.put_strike, T_YEARS, r, iv_dict['put'])
                open_pnl += (t.entry_price_call - c_mark) * t.qty
                open_pnl += (t.entry_price_put - p_mark) * t.qty
            self.portfolio.record_equity(timestamp, open_pnl)
