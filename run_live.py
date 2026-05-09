import asyncio
import signal
from engine.live_engine import LiveEngine
from utils.logger import logger
from config.settings import settings

async def main():
    if not settings.DERIBIT_CLIENT_ID or not settings.TELEGRAM_BOT_TOKEN:
        logger.error("Missing API keys in .env! Please configure them.")
        return

    engine = LiveEngine()
    
    # Graceful Shutdown
    loop = asyncio.get_running_loop()
    
    def stop():
        logger.info("Shutdown signal received...")
        asyncio.create_task(engine.shutdown())
        
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, stop)

    try:
        await engine.startup()
        await engine.run_loop()
    except Exception as e:
        logger.critical(f"Fatal Engine Error: {e}", exc_info=True)
    finally:
        await engine.shutdown()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
