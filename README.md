# Crypto Options Selling Bot (Live Paper Trading)

Production-grade 24/7 forward paper-trading system for Deribit options.

## Features
- **Automated Execution**: Daily entry window (07:00 - 09:00 UTC).
- **Hardened WebSocket**: Reconnection with exponential backoff, heartbeats, and auth.
- **Risk Management**: Combined SL/TP, Max Daily Loss, Liquidity filters.
- **Persistence**: SQLite (SQLAlchemy) for state recovery and trade tracking.
- **Monitoring**: Telegram alerts for entries, exits, errors, and heartbeats.
- **VPS Ready**: Docker support with auto-restart and persistent volumes.

## Installation

1. Clone repo
2. Create `.env` from ` .env.example`
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Local Run
```bash
python run_live.py
```

### Docker Deployment (VPS)
```bash
docker-compose up -d --build
```

## Monitoring & Logs
- **Telegram**: Real-time alerts.
- **Files**: `logs/bot.log`, `logs/trades.log`, `logs/errors.log`.
- **Database**: `storage/trading.db` (SQLite).

## Risk Disclaimer
This system is for **PAPER TRADING ONLY**. Simulation does not account for real-world order book impact or execution delays.
