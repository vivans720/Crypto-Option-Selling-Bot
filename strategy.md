# Crypto Options Short Strangle Backtesting System — Implementation Plan

## Project Goal

Build a Python-based crypto options backtesting engine for a daily expiry short strangle strategy on BTC/ETH using historical options chain data from exchanges like [Deribit](https://www.deribit.com?utm_source=chatgpt.com) or [Delta Exchange](https://www.delta.exchange?utm_source=chatgpt.com).

The system should:

- Fetch historical option chain data
- Simulate daily short strangle trades
- Apply SL/TP/risk management
- Generate detailed performance analytics
- Support parameter optimization

---

# 1. Tech Stack

## Language

- Python 3.11+

## Environment

- Jupyter Notebook / Google Colab initially
- Later convertible into standalone app

## Libraries

### Data Processing

```python
pandas
numpy
datetime
requests
aiohttp
```

### Visualization

```python
matplotlib
plotly
seaborn
```

### Backtesting

```python
vectorbt (optional)
```

### Storage

```python
sqlite3
parquet
```

---

# 2. Project Structure

```plaintext
crypto_options_backtester/

│
├── data/
│   ├── raw/
│   ├── processed/
│   └── cache/
│
├── api/
│   ├── deribit_client.py
│   └── delta_client.py
│
├── strategy/
│   ├── strike_selection.py
│   ├── entry_logic.py
│   ├── exit_logic.py
│   └── risk_management.py
│
├── backtester/
│   ├── engine.py
│   ├── trade_simulator.py
│   └── portfolio.py
│
├── analytics/
│   ├── metrics.py
│   ├── plots.py
│   └── reports.py
│
├── config/
│   └── settings.py
│
├── notebooks/
│
├── main.py
│
└── requirements.txt
```

---

# 3. Core Strategy Logic

## Strategy Type

Daily expiry short strangle.

## Entry Timing

- Entry window:
  - 7:00 AM to 9:00 AM IST

## Instrument

- BTC options initially
- ETH support later

## Expiry Selection

- Next-day expiry

Example:

- If current date is 5th May
- Trade expiry = 6th May

---

# 4. Strike Selection Logic

Implement BOTH modes:

## Mode A — Premium-Based

Find:

- OTM Call near target premium
- OTM Put near target premium

Example:

```python
target_premium = 100
premium_tolerance = 10
```

Select strikes where:

```python
abs(option_price - target_premium) <= premium_tolerance
```

---

## Mode B — Delta-Based (Recommended)

Select:

- Short Call delta:
  - +0.10 to +0.15

- Short Put delta:
  - -0.10 to -0.15

This should be configurable.

---

# 5. Data Requirements

## Required Historical Data

For every option contract:

- Timestamp
- Strike
- Expiry
- Bid
- Ask
- Mark price
- IV
- Delta
- Gamma
- Theta
- Vega
- Underlying price

---

# 6. API Integration

## Deribit Public API

Implement endpoints for:

- Get historical volatility
- Get instruments
- Get order book
- Get historical trades
- Get option chain

### API Features

- Async support
- Retry mechanism
- Rate limiting
- Local caching

---

# 7. Trade Execution Simulation

## Entry

At configured entry time:

1. Fetch option chain
2. Select call + put
3. Sell both
4. Record:
   - Entry premium
   - Greeks
   - Spot price
   - IV

---

## Exit Conditions

Implement all modes:

### Mode A — Individual SL

Example:

```python
SL = entry_price * 2
```

---

### Mode B — Combined Premium SL

Example:

```python
combined_entry = call_entry + put_entry

combined_SL = combined_entry * 1.75
```

---

### Mode C — Profit Target

Example:

```python
TP = 95% decay
```

OR configurable:

```python
TP = 50%
TP = 70%
TP = 90%
```

---

### Mode D — Expiry Exit

Close at expiry settlement.

---

# 8. Risk Management

## Daily Max Loss

Example:

```python
max_daily_loss = 2% account
```

---

## Position Sizing

Implement:

- Fixed margin mode
- Percent risk mode
- Kelly fraction (optional)

---

## Leverage Simulation

Configurable:

```python
10x
25x
50x
100x
200x
```

Also simulate:

- liquidation risk
- margin usage

---

# 9. Slippage + Fees

Must include:

- Trading fees
- Bid/ask spread
- Slippage model

Example:

```python
slippage = 0.25%
```

---

# 10. Market Filters

Implement optional filters:

## Trend Filter

Examples:

- EMA 200
- VWAP
- Market structure

---

## Volatility Filter

Examples:

- IV percentile
- ATR expansion
- Realized volatility

---

## Economic Event Filter

Allow skipping dates manually from CSV.

---

# 11. Backtesting Engine

The engine should:

## Daily Loop

For each day:

1. Check filters
2. Fetch chain
3. Enter trade
4. Simulate candle-by-candle movement
5. Trigger exits
6. Record trade
7. Update balance

---

# 12. Performance Analytics

Generate:

## Core Metrics

- Net PnL
- ROI
- CAGR
- Win rate
- Avg win
- Avg loss
- Profit factor
- Sharpe ratio
- Sortino ratio
- Max drawdown

---

## Risk Metrics

- Tail risk
- Largest loss
- Consecutive losses
- Risk of ruin

---

## Strategy Metrics

- Premium decay efficiency
- Average holding time
- IV crush analysis

---

# 13. Visualization Dashboard

Generate charts:

- Equity curve
- Drawdown curve
- Monthly returns heatmap
- Win/loss distribution
- Greeks exposure over time

Use:

```python
plotly
```

---

# 14. Parameter Optimization

Add grid search for:

- Delta selection
- SL multiplier
- TP percentage
- Entry timing
- IV filters

Example:

```python
delta = [0.1, 0.15, 0.2]
sl = [1.5, 1.75, 2.0]
tp = [50, 70, 90]
```

---

# 15. Output Reports

Generate:

- CSV trade logs
- JSON summaries
- HTML performance reports

---

# 16. Future Enhancements

## Live Trading Module

- Real-time signal engine
- Websocket feeds
- Auto execution

---

## Web Dashboard

Possible stack:

- FastAPI backend
- React frontend

---

## ML Enhancements

Future ideas:

- Volatility prediction
- Regime classification
- Dynamic strike adjustment

---

# 17. MVP Version (Phase 1)

## Minimum Features

Implement FIRST:

### Data

- Deribit API integration
- Historical chain fetching

### Strategy

- Daily short strangle
- Delta strike selection

### Risk

- SL/TP

### Analytics

- PnL
- Drawdown
- Win rate

### Visualization

- Equity curve

---

# 18. Phase 2

Add:

- Greeks analysis
- Multi-expiry testing
- Portfolio margin simulation
- Multi-asset support

---

# 19. Coding Standards

Requirements:

- Modular architecture
- Object-oriented design
- Type hints
- Logging
- Config-driven parameters
- Unit tests for strategy logic

---

# 20. Final Deliverable

The final system should allow:

```python
python main.py --config config/settings.py
```

And output:

- Backtest summary
- Trade logs
- Charts
- Metrics dashboard

with configurable strategy parameters.

# 21. How to get Historial Data

# How To Build Synthetic Historical Option Pricing

The idea is:

You do NOT need historical option chain data initially.

Instead, you:

1. Take historical BTC price candles
2. Assume/estimate implied volatility
3. Use Black-Scholes equations
4. Generate synthetic option premiums historically

This allows you to backtest:

- short strangles
- SL/TP
- theta decay
- delta selection
- IV filters

without needing real historical option chains.

---

# High-Level Workflow

## Step 1 — Get Historical BTC Data

Fetch:

- OHLCV candles

Example sources:

- Binance API
- Yahoo Finance

You need:

```plaintext id="s6g4oj"
timestamp
open
high
low
close
volume
```

Prefer:

- 1 minute
  OR
- 5 minute

data.

---

# Step 2 — Estimate Implied Volatility

You have 3 choices:

## Easiest

Use constant IV:

```python id="ldm3se"
iv = 0.60
```

(60%)

Good for initial testing.

---

## Better

Use rolling historical volatility:

\sigma=\sqrt{252}\cdot std(\ln(P*t/P*{t-1}))

This estimates volatility dynamically.

---

## Advanced

Use Deribit DVOL historical data.

Later improvement.

---

# Step 3 — Generate Synthetic Option Strikes

At each entry time:

- create virtual option strikes

Example:

```python id="gt5k90"
spot = 100000

call_strikes = [102000, 104000, 106000]
put_strikes = [98000, 96000, 94000]
```

---

# Step 4 — Price Options Using Black-Scholes

For CALL:

C=S_0N(d_1)-Ke^{-rt}N(d_2)

For PUT:

P=Ke^{-rt}N(-d_2)-S_0N(-d_1)

Where:

d_1=\frac{\ln(S_0/K)+(r+\sigma^2/2)T}{\sigma\sqrt{T}}

and

d_2=d_1-\sigma\sqrt{T}

---

# Step 5 — Calculate Greeks

Especially:

- delta
- theta
- gamma

Use:

```python id="w5dn84"
scipy.stats.norm
```

This lets you:

- select 10 delta strikes
- simulate theta decay

---

# Step 6 — Select Strikes

Your strategy:

- short 10–15 delta call
- short 10–15 delta put

So:

1. compute deltas
2. filter matching strikes
3. short both

---

# Step 7 — Simulate Intraday Movement

As BTC price changes:

- recompute option prices
- recompute Greeks

This simulates:

- premium expansion
- decay
- SL hits

---

# Step 8 — Apply Risk Management

Example:

```python id="rqy4f7"
SL = 2x premium
TP = 70% decay
```

---

# Step 9 — Track Metrics

Record:

- PnL
- drawdown
- win rate
- expectancy
- largest loss

---

# Why This Approach Is GOOD

Because your strategy mainly depends on:

- volatility
- theta decay
- directional movement

NOT exact orderbook microstructure initially.

This is enough to validate:

- whether strategy has edge
- optimal delta
- best SL
- profitable volatility regimes

---

# Important Limitation

Synthetic pricing will NOT perfectly model:

- slippage
- liquidity
- spread widening
- IV skew
- panic gamma spikes

But it is EXCELLENT for:

- first-stage research

---

# Recommended Development Order

## Phase 1

Simple Black-Scholes backtester.

## Phase 2

Add IV dynamics.

## Phase 3

Add synthetic IV skew.

## Phase 4

Add real historical option chains later.

---

# Prompt To Give The AI

Use this exact prompt:

---

Build a Python-based synthetic historical crypto options backtesting engine for BTC short strangle strategies.

The system should NOT rely on historical option chain APIs initially.

Instead, implement synthetic option pricing using historical BTC price data and the Black-Scholes model.

# Core Requirements

## Historical Data

Fetch historical BTC OHLCV data using:

- Binance API
  OR
- Yahoo Finance

Support:

- 1m
- 5m
- 15m
  timeframes.

---

# Volatility Engine

Implement historical volatility estimation using rolling log returns:

Use annualized volatility calculation.

Allow:

- constant IV mode
- rolling HV mode

Make IV configurable.

---

# Synthetic Option Chain Generation

At each historical timestamp:

1. Generate synthetic option strikes around spot price.
2. Create both CALL and PUT options.
3. Support configurable expiry durations:
   - daily
   - weekly

---

# Black-Scholes Pricing

Implement Black-Scholes option pricing for:

- calls
- puts

Also calculate Greeks:

- delta
- gamma
- theta
- vega

Use scipy.stats.norm.

---

# Strategy Logic

Implement short strangle strategy:

At configured entry time:

1. Select:
   - 10–15 delta OTM call
   - 10–15 delta OTM put

2. Sell both options.

Monitor positions intraday.

---

# Risk Management

Implement:

- individual stop loss
- combined premium stop loss
- take profit
- expiry exit

All parameters configurable.

---

# Backtesting Engine

For each historical candle:

1. Update BTC price
2. Recalculate option prices
3. Recalculate Greeks
4. Check SL/TP
5. Update portfolio

---

# Performance Analytics

Generate:

- equity curve
- drawdown
- win rate
- expectancy
- Sharpe ratio
- max drawdown
- average holding time

---

# Visualization

Use plotly/matplotlib to generate:

- equity curve
- option premium decay
- strike distance charts
- volatility charts

---

# Architecture

Use modular structure:

```plaintext
data/
pricing/
strategy/
backtester/
analytics/
```

---

# Additional Requirements

- Use pandas and numpy heavily.
- Use vectorized calculations where possible.
- Include logging.
- Include configuration file support.
- Make the system extensible for future real historical option chain integration.

---

# Initial Goal

The first milestone is to determine whether daily BTC short strangles using 10–15 delta strikes have positive expectancy under synthetic historical pricing.

# Live Forward Paper Trading System — Implementation Plan

The strategy logic is now validated enough to move into:

# Phase 5 — Live Forward Paper Trading

Goal:
Run the EXACT SAME strategy live using:

* real Deribit option chains
* real IV
* real spreads
* real market behavior

WITHOUT placing real orders.

---

# 1. Core Philosophy

Important:

* Strategy logic remains COMPLETELY unchanged
* Only environment changes:

  * synthetic → live market

The live system should:

* simulate entries/exits
* track paper PnL
* log fills realistically
* run 24/7 automatically

---

# 2. Final Production Architecture

```plaintext id="bn8py0"
crypto_option_live_system/

│
├── app/
│   ├── main.py
│   ├── scheduler.py
│   ├── live_engine.py
│   ├── paper_broker.py
│   ├── position_manager.py
│   ├── risk_manager.py
│   ├── notifications.py
│   └── healthcheck.py
│
├── exchange/
│   ├── deribit_client.py
│   ├── websocket_client.py
│   ├── chain_builder.py
│   └── pricing.py
│
├── strategy/
│   ├── short_strangle.py
│   ├── strike_selector.py
│   └── execution_logic.py
│
├── analytics/
│   ├── pnl_tracker.py
│   ├── trade_logger.py
│   ├── metrics.py
│   └── dashboard.py
│
├── storage/
│   ├── database.py
│   ├── parquet_writer.py
│   └── snapshots/
│
├── config/
│   ├── settings.py
│   └── .env
│
├── logs/
│
├── docker/
│   ├── Dockerfile
│   └── docker-compose.yml
│
├── requirements.txt
└── README.md
```

---

# 3. Live System Workflow

# DAILY FLOW

## 7–9 AM IST

System automatically:

1. Fetches live option chain
2. Selects:

   * short call
   * short put
3. Simulates paper entry
4. Stores:

   * premiums
   * IV
   * Greeks
   * spreads
   * spot price

---

# After Entry

Continuously monitor:

* option premiums
* combined premium
* SL
* TP
* expiry

Then:

* simulate realistic exit
* record PnL
* update equity curve

---

# 4. Live Data Infrastructure

## Use Deribit Websocket API

Do NOT rely only on polling REST APIs.

Use:

* websocket streaming

for:

* premium updates
* IV updates
* Greeks
* spot movement

This greatly improves realism.

---

# 5. Paper Broker System

Implement:

```plaintext id="c79mx0"
PaperBroker
```

Responsibilities:

* virtual positions
* paper fills
* slippage simulation
* spread simulation
* PnL tracking

NO real orders.

---

# 6. Position Monitoring Engine

Must run continuously.

Checks:

```plaintext id="jwhxdr"
while True:
    monitor_positions()
    check_sl_tp()
    update_metrics()
```

Frequency:

```plaintext id="jz0pxs"
1–5 seconds
```

---

# 7. Risk Management

Keep EXACT SAME strategy logic.

Implement:

* existing SL logic
* existing TP logic
* expiry exits

DO NOT modify strategy.

---

# 8. Data Collection (Very Important)

Store EVERYTHING.

## Every Tick/Snapshot

Save:

```plaintext id="xg67gg"
timestamp
spot
call_price
put_price
IV
Greeks
spread
PnL
```

Use:

```plaintext id="40xxyl"
Parquet
```

This becomes your:

# real historical options dataset.

Extremely valuable later.

---

# 9. Notifications

Use Telegram notifications.

Examples:

## Entry

```plaintext id="9fgstf"
[ENTRY]
BTC Spot: 102400
Short Call: 106000C
Short Put: 98500P
Premium: $214
```

---

## Exit

```plaintext id="6rmg42"
[EXIT]
PnL: +$146
Reason: TP Hit
```

---

# 10. Health Monitoring

Very important for live systems.

Implement:

* reconnect logic
* websocket recovery
* API retry handling
* heartbeat monitoring

---

# 11. Dashboard

Build lightweight dashboard showing:

* active positions
* live PnL
* Greeks
* IV
* equity curve
* current drawdown

Use:

```plaintext id="u1ql6q"
Plotly Dash
```

OR:

```plaintext id="pc9g9g"
Streamlit
```

---

# 12. VPS Deployment (24/7)

# BEST OPTION

## [Oracle Cloud Free Tier](https://www.oracle.com/cloud/free/?utm_source=chatgpt.com)

Recommended because:

* free VPS
* reliable
* enough for Python trading bots

---

# Recommended VPS Specs

Minimum:

```plaintext id="5feqdr"
2 vCPU
4GB RAM
Ubuntu 22.04
```

More than enough.

---

# 13. VPS Setup Guide

# Step 1 — Create VPS

Install:

```bash id="ggkgow"
Ubuntu 22.04
```

---

# Step 2 — SSH Into Server

```bash id="7mjqwb"
ssh ubuntu@YOUR_SERVER_IP
```

---

# Step 3 — Install Docker

```bash id="3tfyrc"
sudo apt update
sudo apt install docker.io docker-compose -y
```

---

# Step 4 — Clone Repository

```bash id="3f4d76"
git clone YOUR_GITHUB_REPO
cd repo_name
```

---

# Step 5 — Create .env

```plaintext id="l1u3r8"
DERIBIT_CLIENT_ID=
DERIBIT_CLIENT_SECRET=
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=
```

---

# Step 6 — Build Container

```bash id="fbpr27"
docker compose up -d --build
```

---

# Step 7 — Verify Running

```bash id="3l2ru3"
docker ps
```

---

# 14. Process Reliability

VERY IMPORTANT.

The system MUST:

* auto restart after crashes
* auto restart after VPS reboot

Use:

```plaintext id="r1v7ic"
restart: always
```

inside:

```plaintext id="w7t91k"
docker-compose.yml
```

---

# 15. File Cleanup Plan

Remove all obsolete research/testing files.

# DELETE THESE

## Old Research

```plaintext id="2v4v25"
synthetic_backtester.py
monte_carlo_experiments.py
optimization_old.py
legacy_iv_model.py
```

---

## Old Charts

```plaintext id="5vv8o9"
temporary_heatmaps/
debug_plots/
test_charts/
```

---

## Old CSVs

Delete:

* temporary exports
* duplicate logs
* outdated optimization runs

---

## Remove Notebook Clutter

Delete:

```plaintext id="zjlwmf"
*.ipynb
```

EXCEPT:

```plaintext id="s7p3eq"
research_archive/
```

if you want backup.

---

# KEEP THESE

## Core Production Components

Keep:

```plaintext id="kjlwmr"
deribit_client.py
pricing.py
strike_selector.py
risk_manager.py
paper_broker.py
trade_logger.py
```

---

# 16. Production Mode Requirements

Before going live:

## MUST HAVE

### Logging

* all trades
* all errors
* reconnects
* fills

---

### Persistence

If VPS restarts:

* positions reload correctly
* state restores

---

### Error Handling

No crashes from:

* websocket disconnect
* missing data
* API throttling

---

# 17. VERY IMPORTANT FINAL RULE

For now:

# DO NOT ENABLE REAL ORDER EXECUTION.

Only:

```plaintext id="tx8fjb"
paper trading
```

for several weeks/months.

The live phase is:

# real-world validation phase.

Not profit extraction phase.

---

# 18. Final Goal

The system should become:

```plaintext id="a1g9f8"
Institution-grade crypto options paper trading framework
```

capable of:

* live chain monitoring
* realistic paper execution
* long-term statistics collection
* forward performance validation
* future transition into live execution if validated.
