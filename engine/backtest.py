import pandas as pd
from typing import Dict, Any
from datetime import datetime, timedelta
from engine.portfolio import Portfolio, Trade
from strategy.core import generate_synthetic_chain, select_strikes, check_entry_conditions, calculate_exit
from pricing.volatility import get_dynamic_iv
from pricing.bs_model import calc_option_price
import uuid

def _get_t_years(current_ts: datetime, exit_time_str: str) -> float:
    exit_hour, exit_minute = map(int, exit_time_str.split(':'))
    expiry_dt = current_ts.replace(hour=exit_hour, minute=exit_minute, second=0, microsecond=0)
    if current_ts >= expiry_dt:
        return 0.0
    return (expiry_dt - current_ts).total_seconds() / (365.0 * 24.0 * 3600.0)

class BacktestEngine:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.portfolio = Portfolio(config.get('START_CAPITAL', 10000.0))
        
    def run(self, ohlcv_df: pd.DataFrame):
        r = self.config.get('RISK_FREE_RATE', 0.05)
        exit_time_str = self.config.get('EXIT_TIME', '23:55')
        slippage_pct = self.config.get('SLIPPAGE_PERCENT', 0.01) # 1% of premium
        fees_pct = self.config.get('FEES_PERCENT', 0.0003)
        
        # We need historical vol for dynamic IV. Pre-calculate it.
        # Assuming ohlcv_df has 'close'
        from pricing.volatility import calc_rolling_hv
        if 'rolling_hv' not in ohlcv_df.columns:
            ohlcv_df['rolling_hv'] = calc_rolling_hv(ohlcv_df['close'], window_days=30, periods_per_day=288)
            ohlcv_df['returns_1h'] = ohlcv_df['close'].pct_change(periods=12) # 5m * 12 = 1h
            ohlcv_df.bfill(inplace=True)
            
        # Optimization: use itertuples for 100x speedup over iterrows
        for row in ohlcv_df.itertuples():
            spot = row.close
            timestamp = row.timestamp
            time_str = timestamp.strftime("%H:%M")
            
            # Jump Detection (5m candle)
            # Use abs((close-open)/open) for directional jump or (high-low)/open for volatility jump
            candle_move = abs(row.close - row.open) / row.open
            
            # Dynamic Realism Factors
            current_slippage = slippage_pct
            jump_penalty = 0.0
            
            if candle_move >= 0.08:
                current_slippage *= 10.0 # 10x spread
                jump_penalty = 2.0 # +200% SL slippage
            elif candle_move >= 0.05:
                current_slippage *= 5.0
                jump_penalty = 1.0 # +100%
            elif candle_move >= 0.03:
                current_slippage *= 3.0
                jump_penalty = 0.5 # +50%
            
            T_YEARS = _get_t_years(timestamp, exit_time_str)
            
            # Dynamic IV with Skew
            iv_dict = get_dynamic_iv(spot, getattr(row, 'rolling_hv', 0.60), getattr(row, 'returns_1h', 0.0), self.config)
            
            open_trades = self.portfolio.get_open_trades()
            
            # 1. Manage Exits
            for trade in open_trades:
                c_mark = calc_option_price(spot, trade.call_strike, T_YEARS, r, iv_dict['call'], 'call')
                p_mark = calc_option_price(spot, trade.put_strike, T_YEARS, r, iv_dict['put'], 'put')
                
                # Normal current prices for exit calculation
                current_prices = {
                    'call_mark': c_mark,
                    'put_mark': p_mark
                }
                
                pos_state = {
                    'call_entry_price': trade.entry_price_call,
                    'put_entry_price': trade.entry_price_put
                }
                
                exit_reason = calculate_exit(pos_state, current_prices, self.config.get('SL_MULTIPLIER', 2.0))
                
                if not exit_reason and time_str >= exit_time_str:
                    exit_reason = "EXPIRY"
                
                if exit_reason:
                    # Apply Penalized Slippage if SL hit during Jump
                    final_slippage = current_slippage
                    if "STOP_LOSS" in exit_reason:
                        final_slippage += jump_penalty
                        
                    c_exit = c_mark * (1 + final_slippage)
                    p_exit = p_mark * (1 + final_slippage)
                    
                    trade.close(
                        exit_time=timestamp,
                        exit_call=c_exit,
                        exit_put=p_exit,
                        reason=exit_reason,
                        fees_percent=fees_pct
                    )
            
            # 2. Manage Entries
            if not self.portfolio.get_open_trades():
                if self.config.get('ENTRY_WINDOW_START', '07:00') <= time_str <= self.config.get('ENTRY_WINDOW_END', '09:00'):
                    last_closed = [t for t in self.portfolio.trades if t.status == 'CLOSED']
                    already_traded_today = False
                    if last_closed:
                        last_trade = last_closed[-1]
                        if last_trade.entry_time.date() == timestamp.date():
                            already_traded_today = True
                            
                    if not already_traded_today and T_YEARS > 0:
                        # For entry selection, use average IV to find strikes (strategy logic neutral)
                        avg_iv = (iv_dict['call'] + iv_dict['put']) / 2
                        chain = generate_synthetic_chain(spot, T_YEARS, r, avg_iv)
                        strikes = select_strikes(
                            chain, 
                            self.config.get('TARGET_DELTA_MIN', 0.10),
                            self.config.get('TARGET_DELTA_MAX', 0.15)
                        )
                        
                        if strikes['call'] and strikes['put']:
                            # Use specific skewed IVs for actual execution price
                            # Re-price with skew
                            c_exec_mark = calc_option_price(spot, strikes['call']['strike'], T_YEARS, r, iv_dict['call'], 'call')
                            p_exec_mark = calc_option_price(spot, strikes['put']['strike'], T_YEARS, r, iv_dict['put'], 'put')
                            
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
            if open_trades or time_str == exit_time_str:
                open_pnl = 0.0
                for t in self.portfolio.get_open_trades():
                    c_mark = calc_option_price(spot, t.call_strike, T_YEARS, r, iv_dict['call'], 'call')
                    p_mark = calc_option_price(spot, t.put_strike, T_YEARS, r, iv_dict['put'], 'put')
                    open_pnl += (t.entry_price_call - c_mark) * t.qty
                    open_pnl += (t.entry_price_put - p_mark) * t.qty
                self.portfolio.record_equity(timestamp, open_pnl)
