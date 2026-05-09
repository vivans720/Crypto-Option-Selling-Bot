import logging
import os
from telegram import Bot
from telegram.constants import ParseMode
import asyncio

logger = logging.getLogger(__name__)

class TelegramNotifier:
    def __init__(self, token: str, chat_id: str):
        self.token = token
        self.chat_id = chat_id
        self.bot = Bot(token=token) if token and chat_id else None

    async def send_message(self, text: str):
        if not self.bot:
            logger.warning(f"Telegram not configured. Msg: {text}")
            return
        try:
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=text,
                parse_mode=ParseMode.HTML
            )
        except Exception as e:
            logger.error(f"Telegram error: {e}")

    async def notify_entry(self, trade_id: str, spot: float, call_strike: float, put_strike: float, premium: float):
        msg = (
            f"<b>[ENTRY]</b>\n"
            f"Trade: {trade_id}\n"
            f"BTC Spot: ${spot:,.2f}\n"
            f"Short Call: {call_strike}C\n"
            f"Short Put: {put_strike}P\n"
            f"Total Premium: ${premium:,.2f}"
        )
        await self.send_message(msg)

    async def notify_exit(self, trade_id: str, pnl: float, reason: str):
        status = "PROFIT" if pnl > 0 else "LOSS"
        msg = (
            f"<b>[EXIT - {status}]</b>\n"
            f"Trade: {trade_id}\n"
            f"PnL: ${pnl:,.2f}\n"
            f"Reason: {reason}"
        )
        await self.send_message(msg)
