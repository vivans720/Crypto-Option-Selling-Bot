import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    # API Keys
    DERIBIT_CLIENT_ID: Optional[str] = None
    DERIBIT_CLIENT_SECRET: Optional[str] = None
    TELEGRAM_BOT_TOKEN: Optional[str] = None
    TELEGRAM_CHAT_ID: Optional[str] = None
    
    # Engine Settings
    TESTNET: bool = True
    LOG_LEVEL: str = "INFO"
    DB_PATH: str = "sqlite:///storage/trading.db"
    
    # Backtest / Paper Configuration
    TRADING_SYMBOL: str = "BTC"
    TARGET_DELTA_MIN: float = 0.10
    TARGET_DELTA_MAX: float = 0.15
    START_CAPITAL: float = 10000.0
    
    # Timing (UTC)
    ENTRY_WINDOW_START: str = "07:00"
    ENTRY_WINDOW_END: str = "09:00"
    
    # Risk Management
    SL_MULTIPLIER: float = 2.0
    FEES_PERCENT: float = 0.0003
    SLIPPAGE_PERCENT: float = 0.0025
    MAX_DAILY_LOSS: float = 500.0
    MAX_OPEN_POSITIONS: int = 1
    LIQUIDITY_MIN_BID_SIZE: float = 0.1
    IV_MIN: float = 0.3
    IV_MAX: float = 1.5
    STRATEGY_COOLDOWN_MINUTES: int = 60

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
