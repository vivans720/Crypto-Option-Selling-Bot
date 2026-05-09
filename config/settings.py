import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
from pathlib import Path

class Settings(BaseSettings):
    # Paths
    BASE_DIR: Path = Path(__file__).parent.parent
    DATA_RAW_DIR: Path = BASE_DIR / "data" / "raw"
    DATA_PROCESSED_DIR: Path = BASE_DIR / "data" / "processed"
    DATA_CACHE_DIR: Path = BASE_DIR / "data" / "cache"
    DATA_EXPORTS_DIR: Path = BASE_DIR / "data" / "exports"
    DATA_PARQUET_DIR: Path = BASE_DIR / "data" / "parquet"
    
    RESEARCH_REPORTS_DIR: Path = BASE_DIR / "research" / "reports"
    RESEARCH_RESULTS_DIR: Path = BASE_DIR / "research" / "results"
    
    # Backtest / Paper Configuration
    TRADING_SYMBOL: str = "BTC"
    TARGET_DELTA_MIN: float = 0.10
    TARGET_DELTA_MAX: float = 0.15
    START_CAPITAL: float = 10000.0
    
    # Risk Management
    SL_MULTIPLIER: float = 2.0
    FEES_PERCENT: float = 0.0003  # Default for Maker/Taker blended
    SLIPPAGE_PERCENT: float = 0.0025
    MAX_DAILY_LOSS_PCT: float = 0.05
    MAX_OPEN_POSITIONS: int = 1
    IV_MIN: float = 0.3
    IV_MAX: float = 1.5

    # Strategy Parameters
    DTE_MIN: int = 0
    DTE_MAX: int = 7
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
