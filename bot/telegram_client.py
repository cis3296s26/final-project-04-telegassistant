# bot/telegram_client.py
# ============================================================
# TeleGAssistant — Telegram Bot Client
# Owned by: Bot & Interface Engineer
# ============================================================
import asyncio
import logging
import re
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from interfaces import AbstractBot

logger = logging.getLogger(__name__)


# ------------------------------------------------------------------ #
# Utility                                                             #
# ------------------------------------------------------------------ #

def escape_md2(text: str) -> str:
    """
    Escape all Telegram MarkdownV2 special characters in a plain string.

    Use this on any dynamic content (user names, task titles, etc.)
    before embedding it in a MarkdownV2-formatted reply_text call.

    NOT needed for send_message() — that method sends plain text.
    """
    return re.sub(r'([_*\[\]()~`>#+\-=|{}.!\\])', r'\\\1', text)


# MarkdownV2 formatted — special chars in these strings are intentionally escaped.
HELP_TEXT = (
    "*TeleGAssistant Commands*\n\n"
    "/start — Register with the bot\n"
    "/help — Show this list\n"
    "/status — Check if the bot is online\n"
    "/briefing — Get your daily briefing now"
)


# ------------------------------------------------------------------ #
# Bot client                                                          #
# ------------------------------------------------------------------ #

class TelegramBotClient(AbstractBot):

    def __init__(self, token: str, db=None, ai=None):
        """
        token — Telegram bot token from BotFather (.env)
        db    — AbstractDB instance; needed for /start and /briefing
        ai    — AbstractAI instance; needed for /briefing
        Both are optional so the bot still starts even if other layers
        aren't wired yet.
        """
        self._db  = db
        self._ai  = ai
        self._app = Application.builder().token(token).build()
        self._register_handlers()

    # ---------------------------------------------------------------- #
    # Handler registration                                              #
    # ---------------------------------------------------------------- #

    def _register_handlers(self):
        self._app.add_handler(CommandHandler("start",    self._handle_start))
        self._app.add_handler(CommandHandler("help",     self._handle_help))
        self._app.add_handler(CommandHandler("status",   self._handle_status))
        self._app.add_handler(CommandHandler("briefing", self._handle_briefing))
        self._app.add_error_handler(self._handle_error)

    # ---------------------------------------------------------------- #
    # Command handlers                                                  #
    # ---------------------------------------------------------------- #

    async def _handle_start(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """
        /start — register the user and send a welcome message.
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

        safe_name = escape_md2(name)
        await update.message.reply_text(
            f"Hi {safe_name}\\! You're now registered with TeleGAssistant\\.\n\n"
            "Send /help to see what I can do\\.",
            parse_mode="MarkdownV2",
        )

    async def _handle_help(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """/help — list available commands."""
        await update.message.reply_text(HELP_TEXT, parse_mode="MarkdownV2")

    async def _handle_status(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """/status — confirm the bot is reachable."""
        await update.message.reply_text(
            "Bot is online and running\\.", parse_mode="MarkdownV2"
        )

    async def _handle_briefing(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """
        /briefing — trigger a briefing for the requesting user immediately.

        Fails gracefully at every step: DB unavailable, user not registered,
        AI down, send failure — the user always gets a readable message.
        """
        chat_id = update.effective_chat.id

        if self._db is None or self._ai is None:
            await update.message.reply_text(
                "Briefing unavailable — bot is not fully configured yet\\.",
                parse_mode="MarkdownV2",
            )
            return

        # --- look up the requesting user ---
        try:
            users = self._db.get_active_users()
            user  = next((u for u in users if u["telegram_id"] == chat_id), None)
        except Exception as e:
            logger.error(f"/briefing: DB error for chat_id={chat_id}: {e}")
            await update.message.reply_text(
                "Couldn't reach the database\\. Try again in a moment\\.",
                parse_mode="MarkdownV2",
            )
            return

        if user is None:
            await update.message.reply_text(
                "You're not registered yet\\. Send /start first\\.",
                parse_mode="MarkdownV2",
            )
            return

        # --- generate and send ---
        await update.message.reply_text(
            "Generating your briefing\\.\\.\\.", parse_mode="MarkdownV2"
        )

        try:
            from jobs.briefing import send_briefing_for_user
            await send_briefing_for_user(user, self._db, self._ai, self)
        except Exception as e:
            logger.error(f"/briefing: pipeline failed for chat_id={chat_id}: {e}")
            await update.message.reply_text(
                "Something went wrong generating your briefing\\. Try again later\\.",
                parse_mode="MarkdownV2",
            )

    async def _handle_error(
        self, update: object, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """
        Global fallback for any unhandled exception inside a handler.
        Logs the error and tells the user something went wrong.
        """
        logger.error(f"Unhandled bot error: {context.error}", exc_info=context.error)
        if hasattr(update, "effective_message") and update.effective_message:
            await update.effective_message.reply_text(
                "Something went wrong on my end\\. Please try again\\.",
                parse_mode="MarkdownV2",
            )

    # ---------------------------------------------------------------- #
    # AbstractBot interface                                             #
    # ---------------------------------------------------------------- #

    async def send_message(self, chat_id: int, text: str) -> None:
        """
        Send a message to a Telegram user.

        Sends as plain text (no parse_mode) so briefing content —
        which may include emoji, punctuation, or AI-generated text —
        always renders safely regardless of what it contains.

        Raises on failure so the briefing pipeline's retry loop works.
        Splits messages longer than Telegram's 4096-char limit.
        """
        MAX_LEN = 4096
        chunks = [text[i : i + MAX_LEN] for i in range(0, len(text), MAX_LEN)]
        for chunk in chunks:
            await self._app.bot.send_message(chat_id=chat_id, text=chunk)
        logger.info(f"send_message: delivered to chat_id={chat_id}")

    async def start_polling(self) -> None:
        """
        Start the Telegram polling loop. Runs until cancelled by app.py.
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
