# bot/telegram_client.py
# ============================================================
# TeleGAssistant — Telegram Bot Client
# Owned by: Bot & Interface Engineer
# ============================================================
import asyncio
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from interfaces import AbstractBot

logger = logging.getLogger(__name__)

HELP_TEXT = (
    "TeleGAssistant Commands:\n\n"
    "/start  — Register with the bot\n"
    "/help   — Show this list\n"
    "/status — Check if the bot is online"
)


class TelegramBotClient(AbstractBot):

    def __init__(self, token: str, db=None):
        """
        token — Telegram bot token from BotFather (loaded from .env)
        db    — AbstractDB instance; required for /start to persist users.
                Optional so the bot still runs if DB isn't wired yet.
        """
        self._db = db
        self._app = Application.builder().token(token).build()
        self._register_handlers()

    # ------------------------------------------------------------------ #
    # Handler registration — called once at construction                  #
    # ------------------------------------------------------------------ #

    def _register_handlers(self):
        self._app.add_handler(CommandHandler("start",  self._handle_start))
        self._app.add_handler(CommandHandler("help",   self._handle_help))
        self._app.add_handler(CommandHandler("status", self._handle_status))

    # ------------------------------------------------------------------ #
    # Command handlers                                                     #
    # ------------------------------------------------------------------ #

    async def _handle_start(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """
        /start — register the user and send a welcome message.

        Captures the Telegram chat ID and display name, then persists
        them via db.register_user().  If the DB is unavailable we still
        reply so the user isn't left hanging.
        """
        user    = update.effective_user
        chat_id = update.effective_chat.id
        name    = user.first_name or user.username or "there"

        if self._db is not None:
            try:
                self._db.register_user(telegram_id=chat_id, name=name)
                logger.info(f"/start: registered {name} (chat_id={chat_id})")
            except Exception as e:
                logger.error(f"/start: DB register_user failed for {chat_id}: {e}")

        await update.message.reply_text(
            f"Hi {name}! You're now registered with TeleGAssistant.\n\n"
            "Send /help to see what I can do."
        )

    async def _handle_help(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """/help — list available commands."""
        await update.message.reply_text(HELP_TEXT)

    async def _handle_status(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """/status — confirm the bot is reachable."""
        await update.message.reply_text("Bot is online and running.")

    # ------------------------------------------------------------------ #
    # AbstractBot interface                                                #
    # ------------------------------------------------------------------ #

    async def send_message(self, chat_id: int, text: str) -> None:
        """
        Send a message to a Telegram user.

        Splits messages longer than Telegram's 4096-character limit.
        Raises on failure so the briefing pipeline can retry.
        """
        MAX_LEN = 4096
        chunks = [text[i : i + MAX_LEN] for i in range(0, len(text), MAX_LEN)]
        for chunk in chunks:
            await self._app.bot.send_message(
                chat_id=chat_id,
                text=chunk,
                parse_mode="Markdown",
            )
        logger.info(f"send_message: delivered to chat_id={chat_id}")

    async def start_polling(self) -> None:
        """
        Start the Telegram polling loop.  Runs until cancelled by app.py.
        Handles graceful shutdown so no messages are dropped mid-flight.
        """
        logger.info("Telegram bot polling started")
        await self._app.initialize()
        await self._app.start()
        await self._app.updater.start_polling(drop_pending_updates=True)
        try:
            while True:
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            pass
        finally:
            logger.info("Stopping bot polling...")
            await self._app.updater.stop()
            await self._app.stop()
            await self._app.shutdown()
