# bot/telegram_client.py
import logging
from telegram import Bot
from telegram.ext import Application
from interfaces import AbstractBot

logger = logging.getLogger(__name__)


class TelegramBotClient(AbstractBot):

    def __init__(self, token: str):
        self._token = token
        self._bot = Bot(token=token)
        self._app = Application.builder().token(token).build()

    async def send_message(self, chat_id: int, text: str) -> None:
        await self._bot.send_message(
            chat_id=chat_id,
            text=text,
            parse_mode="Markdown",
        )
        logger.info(f"Message sent to chat_id {chat_id}")

    async def start_polling(self) -> None:
        logger.info("Telegram bot polling started")
        await self._app.initialize()
        await self._app.start()
        await self._app.updater.start_polling()
        # Keep running until cancelled
        import asyncio
        while True:
            await asyncio.sleep(1)
