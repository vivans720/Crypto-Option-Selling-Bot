import os
from dotenv import load_dotenv

load_dotenv()

# API Configuration
DERIBIT_CLIENT_ID = os.getenv("DERIBIT_CLIENT_ID")
DERIBIT_CLIENT_SECRET = os.getenv("DERIBIT_CLIENT_SECRET")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Backtest Configuration
TRADING_SYMBOL = "BTC"
TARGET_DELTA_MIN = 0.10
TARGET_DELTA_MAX = 0.15

# Entry Window (IST converted to UTC or just keep as string for logic)
ENTRY_WINDOW_START = "07:00"
ENTRY_WINDOW_END = "09:00"

# Risk Management
SL_MULTIPLIER = 2.0  # Stop loss at 2x entry premium
FEES_PERCENT = 0.0003  # 0.03% fee per leg
SLIPPAGE_PERCENT = 0.0025  # 0.25% slippage

START_CAPITAL = 10000.0
