import logging
import sys
import os
from logging.handlers import RotatingFileHandler

def setup_logger(name: str, log_file: str = "logs/bot.log", level=logging.INFO):
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # File Handler
    file_handler = RotatingFileHandler(
        log_file, maxBytes=10*1024*1024, backupCount=5
    )
    file_handler.setFormatter(formatter)

    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    if not logger.handlers:
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
    
    return logger

# Pre-configured loggers
logger = setup_logger("bot")
trade_logger = setup_logger("trade", "logs/trades.log")
error_logger = setup_logger("error", "logs/errors.log", level=logging.ERROR)
