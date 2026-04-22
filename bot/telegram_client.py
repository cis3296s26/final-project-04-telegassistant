# bot/telegram_client.py
# ============================================================
# TeleGAssistant — Telegram Bot Client
# Owned by: Bot & Interface Engineer
# ============================================================
import asyncio
import logging
import re
import os
from datetime import datetime, date

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    filters,
    ContextTypes,
)
from interfaces import AbstractBot
from bot.ui import build_calendar, build_hour_picker, build_minute_picker

logger = logging.getLogger(__name__)

GMAIL_SCOPES     = ["https://www.googleapis.com/auth/gmail.readonly"]
CREDENTIALS_PATH = "credentials.json"
TOKEN_PATH       = "token.json"

_awaiting_gmail_code: set[int] = set()
_gmail_flows: dict[int, object] = {}  # chat_id -> Flow instance, kept alive for code exchange

# ConversationHandler states
(
    ADDTASK_NAME,
    ADDTASK_DATE,
    ADDTASK_HOUR,
    ADDTASK_MIN,
    ADDTASK_DESC,
    REMINDME_TEXT,
    REMINDME_DATE,
    REMINDME_HOUR,
    REMINDME_MIN,
    REMINDME_RECUR,
) = range(10)


# ------------------------------------------------------------------ #
# Utility                                                             #
# ------------------------------------------------------------------ #

def escape_md2(text: str) -> str:
    return re.sub(r'([_*\[\]()~`>#+\-=|{}.!\\])', r'\\\1', text)


HELP_TEXT = (
    "*TeleGAssistant Commands*\n\n"
    "/start — Register with the bot\n"
    "/help — Show this list\n"
    "/status — Check if the bot is online\n"
    "/briefing — Get your daily briefing now\n"
    "/emails — Triage your unread emails\n"
    "/tasks — View your pending tasks\n"
    "/addtask — Add a new task\n"
    "/removetask — Remove or complete a task\n"
    "/remindme — Set a custom reminder\n"
    "/setupgmail — Connect your Gmail account"
)


# ------------------------------------------------------------------ #
# Bot client                                                          #
# ------------------------------------------------------------------ #

class TelegramBotClient(AbstractBot):

    def __init__(self, token: str, db=None, ai=None):
        self._db  = db
        self._ai  = ai
        self._app = Application.builder().token(token).build()
        self._register_handlers()

    # ---------------------------------------------------------------- #
    # Handler registration                                              #
    # ---------------------------------------------------------------- #

    def _register_handlers(self):
        # /addtask conversation
        addtask_conv = ConversationHandler(
            entry_points=[CommandHandler("addtask", self._addtask_start)],
            states={
                ADDTASK_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, self._addtask_name)],
                ADDTASK_DATE: [CallbackQueryHandler(self._addtask_date, pattern=r"^CAL_")],
                ADDTASK_HOUR: [CallbackQueryHandler(self._addtask_hour, pattern=r"^TIME_HOUR\|")],
                ADDTASK_MIN:  [CallbackQueryHandler(self._addtask_min,  pattern=r"^TIME_MIN\|")],
                ADDTASK_DESC: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self._addtask_desc),
                    CommandHandler("skip", self._addtask_desc_skip),
                ],
            },
            fallbacks=[CommandHandler("cancel", self._conv_cancel)],
            name="addtask",
            persistent=False,
            per_message=False,
        )

        # /remindme conversation
        remindme_conv = ConversationHandler(
            entry_points=[CommandHandler("remindme", self._remindme_start)],
            states={
                REMINDME_TEXT:  [MessageHandler(filters.TEXT & ~filters.COMMAND, self._remindme_text)],
                REMINDME_DATE:  [CallbackQueryHandler(self._remindme_date,  pattern=r"^CAL_")],
                REMINDME_HOUR:  [CallbackQueryHandler(self._remindme_hour,  pattern=r"^TIME_HOUR\|")],
                REMINDME_MIN:   [CallbackQueryHandler(self._remindme_min,   pattern=r"^TIME_MIN\|")],
                REMINDME_RECUR: [CallbackQueryHandler(self._remindme_recur, pattern=r"^RECUR\|")],
            },
            fallbacks=[CommandHandler("cancel", self._conv_cancel)],
            name="remindme",
            persistent=False,
            per_message=False,
        )

        self._app.add_handler(addtask_conv)
        self._app.add_handler(remindme_conv)

        self._app.add_handler(CommandHandler("start",      self._handle_start))
        self._app.add_handler(CommandHandler("help",       self._handle_help))
        self._app.add_handler(CommandHandler("status",     self._handle_status))
        self._app.add_handler(CommandHandler("briefing",   self._handle_briefing))
        self._app.add_handler(CommandHandler("tasks",      self._handle_tasks))
        self._app.add_handler(CommandHandler("removetask", self._handle_removetask))
        self._app.add_handler(CommandHandler("emails",     self._handle_emails))
        self._app.add_handler(CommandHandler("setupgmail", self._handle_setup_gmail))

        # Task completion Yes/No callbacks
        self._app.add_handler(CallbackQueryHandler(self._handle_task_done,      pattern=r"^TASK_DONE\|"))
        self._app.add_handler(CallbackQueryHandler(self._handle_task_keep,      pattern=r"^TASK_KEEP\|"))
        # Remove task callbacks
        self._app.add_handler(CallbackQueryHandler(self._handle_remove_confirm, pattern=r"^REMOVE_TASK\|"))

        self._app.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND, self._handle_text
        ))
        self._app.add_error_handler(self._handle_error)

    # ---------------------------------------------------------------- #
    # /start                                                            #
    # ---------------------------------------------------------------- #

    async def _handle_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user    = update.effective_user
        chat_id = update.effective_chat.id
        name    = user.first_name or user.username or "there"

        if self._db is not None:
            try:
                self._db.register_user(telegram_id=chat_id, name=name)
            except Exception as e:
                logger.error(f"/start: DB error for {chat_id}: {e}")

        safe_name = escape_md2(name)
        await update.message.reply_text(
            f"Hi {safe_name}\\! You're now registered with TeleGAssistant\\.\n\n"
            "Send /help to see what I can do\\.",
            parse_mode="MarkdownV2",
        )

    # ---------------------------------------------------------------- #
    # /help, /status                                                    #
    # ---------------------------------------------------------------- #

    async def _handle_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(HELP_TEXT, parse_mode="MarkdownV2")

    async def _handle_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("Bot is online and running\\.", parse_mode="MarkdownV2")

    # ---------------------------------------------------------------- #
    # /briefing                                                         #
    # ---------------------------------------------------------------- #

    async def _handle_briefing(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_chat.id

        if self._db is None or self._ai is None:
            await update.message.reply_text(
                "Briefing unavailable — bot is not fully configured yet\\.",
                parse_mode="MarkdownV2",
            )
            return

        try:
            users = self._db.get_active_users()
            user  = next((u for u in users if u["telegram_id"] == chat_id), None)
        except Exception as e:
            logger.error(f"/briefing: DB error for {chat_id}: {e}")
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

        await update.message.reply_text(
            "Generating your briefing\\.\\.\\.", parse_mode="MarkdownV2"
        )

        try:
            from jobs.briefing import send_briefing_for_user
            await send_briefing_for_user(user, self._db, self._ai, self)
        except Exception as e:
            logger.error(f"/briefing: pipeline failed for {chat_id}: {e}")
            await update.message.reply_text(
                "Something went wrong generating your briefing\\. Try again later\\.",
                parse_mode="MarkdownV2",
            )

    # ---------------------------------------------------------------- #
    # /emails                                                           #
    # ---------------------------------------------------------------- #

    async def _handle_emails(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        from ai.gmail_client import get_recent_emails, is_connected

        if not is_connected():
            await update.message.reply_text(
                "Gmail isn't connected yet. Send /setupgmail to set it up."
            )
            return

        await update.message.reply_text("Fetching and triaging your emails...")

        emails = await get_recent_emails()

        if emails is None:
            await update.message.reply_text(
                "Could not reach Gmail. Check that token.json is valid."
            )
            return

        if not emails:
            await update.message.reply_text("No unread emails in the last 3 days.")
            return

        try:
            result = await self._ai.triage_emails(emails)
            await update.message.reply_text(f"📧 Email Triage — {len(emails)} scanned\n\n{result}")
        except Exception as e:
            logger.error(f"/emails triage failed: {e}")
            # Fallback — just list them raw
            lines = [f"📧 Unread Emails ({len(emails)})\n"]
            for i, em in enumerate(emails, 1):
                lines.append(f"{i}. {em['from']} — {em['subject']}")
            await update.message.reply_text("\n".join(lines))

    # ---------------------------------------------------------------- #
    # /tasks                                                            #
    # ---------------------------------------------------------------- #

    async def _handle_tasks(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_chat.id
        user = self._db.get_user_by_telegram_id(chat_id) if self._db else None

        if not user:
            await update.message.reply_text("Send /start to register first.")
            return

        tasks = self._db.get_all_tasks_for_user(user["id"])

        if not tasks:
            await update.message.reply_text("You have no pending tasks.")
            return

        today = date.today()
        lines = ["Your pending tasks:\n"]
        for t in tasks:
            days_left = (t["due_date"] - today).days
            if days_left == 0:
                when = "due TODAY"
            elif days_left < 0:
                when = f"overdue by {abs(days_left)}d"
            else:
                when = f"due in {days_left}d"

            due_str = t["due_datetime"].strftime("%b %d, %I:%M %p")
            desc    = f" — {t['description']}" if t["description"] else ""
            lines.append(f"• {t['title']} ({when}, {due_str}){desc}")

        await update.message.reply_text("\n".join(lines))

    # ---------------------------------------------------------------- #
    # /addtask conversation                                             #
    # ---------------------------------------------------------------- #

    async def _addtask_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_chat.id
        user = self._db.get_user_by_telegram_id(chat_id) if self._db else None
        if not user:
            await update.message.reply_text("Send /start to register first.")
            return ConversationHandler.END

        context.user_data.pop("remindme", None)
        context.user_data["addtask"] = {}
        await update.message.reply_text("What's the name of the task?")
        return ADDTASK_NAME

    async def _addtask_name(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        context.user_data["addtask"]["title"] = update.message.text.strip()
        today = date.today()
        await update.message.reply_text(
            "Pick a due date:",
            reply_markup=build_calendar(today.year, today.month),
        )
        return ADDTASK_DATE

    async def _addtask_date(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        data = query.data

        if data == "CAL_IGNORE":
            return ADDTASK_DATE

        if data.startswith("CAL_NAV|"):
            year, month = map(int, data.split("|")[1].split("-"))
            await query.edit_message_reply_markup(
                reply_markup=build_calendar(year, month)
            )
            return ADDTASK_DATE

        selected_date = data.split("|")[1]
        context.user_data["addtask"]["date"] = selected_date
        await query.edit_message_text(
            f"Date: {selected_date}\n\nPick an hour:",
            reply_markup=build_hour_picker(),
        )
        return ADDTASK_HOUR

    async def _addtask_hour(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        hour = query.data.split("|")[1]
        context.user_data["addtask"]["hour"] = hour
        await query.edit_message_text(
            f"Date: {context.user_data['addtask']['date']}  Hour: {hour}\n\nPick minutes:",
            reply_markup=build_minute_picker(hour),
        )
        return ADDTASK_MIN

    async def _addtask_min(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        minute = query.data.split("|")[1]
        d = context.user_data["addtask"]
        d["minute"] = minute
        dt_str = f"{d['date']} {d['hour']}:{minute}"
        await query.edit_message_text(
            f"Task: {d['title']}\nDue: {dt_str}\n\nAdd a description? (or send /skip)"
        )
        return ADDTASK_DESC

    async def _addtask_desc(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        context.user_data["addtask"]["desc"] = update.message.text.strip()
        return await self._addtask_save(update, context)

    async def _addtask_desc_skip(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        context.user_data["addtask"]["desc"] = ""
        return await self._addtask_save(update, context)

    async def _addtask_save(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_chat.id
        d = context.user_data.pop("addtask", {})

        dt   = datetime.strptime(f"{d['date']} {d['hour']}:{d['minute']}", "%Y-%m-%d %H:%M")
        user = self._db.get_user_by_telegram_id(chat_id)
        self._db.add_task(
            user_id=user["id"],
            title=d["title"],
            due_datetime=dt,
            description=d.get("desc", ""),
        )

        due_str = dt.strftime("%B %d at %I:%M %p")
        await update.message.reply_text(f"Task added: {d['title']}\nDue: {due_str}")
        return ConversationHandler.END

    # ---------------------------------------------------------------- #
    # /removetask                                                       #
    # ---------------------------------------------------------------- #

    async def _handle_removetask(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_chat.id
        user = self._db.get_user_by_telegram_id(chat_id) if self._db else None

        if not user:
            await update.message.reply_text("Send /start to register first.")
            return

        tasks = self._db.get_all_tasks_for_user(user["id"])

        if not tasks:
            await update.message.reply_text("You have no pending tasks to remove.")
            return

        keyboard = []
        for t in tasks:
            due_str = t["due_datetime"].strftime("%b %d %I:%M %p")
            keyboard.append([InlineKeyboardButton(
                f"{t['title']} — {due_str}",
                callback_data=f"REMOVE_TASK|{t['id']}",
            )])

        await update.message.reply_text(
            "Which task do you want to remove?",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

    async def _handle_remove_confirm(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        task_id = int(query.data.split("|")[1])

        try:
            self._db.remove_task(task_id)
            await query.edit_message_text("Task removed.")
        except Exception as e:
            logger.error(f"remove_task failed: {e}")
            await query.edit_message_text("Could not remove that task. Try again.")

    # ---------------------------------------------------------------- #
    # Task completion callbacks (fired by reminder notifications)      #
    # ---------------------------------------------------------------- #

    async def _handle_task_done(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        task_id = int(query.data.split("|")[1])
        try:
            self._db.remove_task(task_id)
            await query.edit_message_text("Nice work — task marked complete and removed.")
        except Exception as e:
            logger.error(f"task_done failed: {e}")
            await query.edit_message_text("Could not update the task. Try /removetask manually.")

    async def _handle_task_keep(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        await query.edit_message_text("Got it — task is still on your list.")

    # ---------------------------------------------------------------- #
    # /remindme conversation                                            #
    # ---------------------------------------------------------------- #

    async def _remindme_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_chat.id
        user = self._db.get_user_by_telegram_id(chat_id) if self._db else None
        if not user:
            await update.message.reply_text("Send /start to register first.")
            return ConversationHandler.END

        context.user_data.pop("addtask", None)
        context.user_data["remindme"] = {}
        await update.message.reply_text("What do you want to be reminded about?")
        return REMINDME_TEXT

    async def _remindme_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        context.user_data["remindme"]["text"] = update.message.text.strip()
        today = date.today()
        await update.message.reply_text(
            "Pick a date:",
            reply_markup=build_calendar(today.year, today.month),
        )
        return REMINDME_DATE

    async def _remindme_date(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        data = query.data

        if data == "CAL_IGNORE":
            return REMINDME_DATE

        if data.startswith("CAL_NAV|"):
            year, month = map(int, data.split("|")[1].split("-"))
            await query.edit_message_reply_markup(
                reply_markup=build_calendar(year, month)
            )
            return REMINDME_DATE

        selected_date = data.split("|")[1]
        context.user_data["remindme"]["date"] = selected_date
        await query.edit_message_text(
            f"Date: {selected_date}\n\nPick an hour:",
            reply_markup=build_hour_picker(),
        )
        return REMINDME_HOUR

    async def _remindme_hour(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        hour = query.data.split("|")[1]
        context.user_data["remindme"]["hour"] = hour
        await query.edit_message_text(
            f"Date: {context.user_data['remindme']['date']}  Hour: {hour}\n\nPick minutes:",
            reply_markup=build_minute_picker(hour),
        )
        return REMINDME_MIN

    async def _remindme_min(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        minute = query.data.split("|")[1]
        d = context.user_data["remindme"]
        d["minute"] = minute
        dt_str = f"{d['date']} {d['hour']}:{minute}"

        recur_keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("One-time", callback_data="RECUR|none"),
            InlineKeyboardButton("Daily",    callback_data="RECUR|daily"),
            InlineKeyboardButton("Weekly",   callback_data="RECUR|weekly"),
        ]])
        await query.edit_message_text(
            f"Reminder: {d['text']}\nWhen: {dt_str}\n\nHow often?",
            reply_markup=recur_keyboard,
        )
        return REMINDME_RECUR

    async def _remindme_recur(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        recurrence = query.data.split("|")[1]
        chat_id = update.effective_chat.id

        d = context.user_data.pop("remindme", {})
        dt   = datetime.strptime(f"{d['date']} {d['hour']}:{d['minute']}", "%Y-%m-%d %H:%M")
        user = self._db.get_user_by_telegram_id(chat_id)
        self._db.add_reminder(
            user_id=user["id"],
            text=d["text"],
            remind_at=dt,
            recurrence=recurrence,
        )

        recur_label = {"none": "one-time", "daily": "daily", "weekly": "weekly"}[recurrence]
        due_str = dt.strftime("%B %d at %I:%M %p")
        await query.edit_message_text(
            f"Reminder set ({recur_label}): {d['text']}\nFirst fire: {due_str}"
        )
        return ConversationHandler.END

    # ---------------------------------------------------------------- #
    # /setupgmail                                                       #
    # ---------------------------------------------------------------- #

    async def _handle_setup_gmail(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_chat.id

        if not os.path.exists(CREDENTIALS_PATH):
            await update.message.reply_text(
                "Gmail setup is not configured on this server yet."
            )
            return

        if os.path.exists(TOKEN_PATH):
            await update.message.reply_text(
                "Gmail is already connected. Your briefings include unread emails."
            )
            return

        try:
            from google_auth_oauthlib.flow import Flow
            flow = Flow.from_client_secrets_file(
                CREDENTIALS_PATH,
                scopes=GMAIL_SCOPES,
                redirect_uri="urn:ietf:wg:oauth:2.0:oob",
            )
            auth_url, _ = flow.authorization_url(access_type="offline", prompt="consent")
            _awaiting_gmail_code.add(chat_id)
            _gmail_flows[chat_id] = flow  # keep same instance for code exchange
            await update.message.reply_text(
                f"To connect Gmail, open this link and authorize access:\n\n{auth_url}\n\n"
                "Then paste the code Google gives you back here."
            )
        except Exception as e:
            logger.error(f"/setupgmail error: {e}")
            await update.message.reply_text(
                "Something went wrong generating the Gmail auth link. Try again later."
            )

    # ---------------------------------------------------------------- #
    # Conversation cancel                                               #
    # ---------------------------------------------------------------- #

    async def _conv_cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        context.user_data.pop("addtask",  None)
        context.user_data.pop("remindme", None)
        await update.message.reply_text("Cancelled.")
        return ConversationHandler.END

    # ---------------------------------------------------------------- #
    # Plain text handler (Gmail OAuth code)                            #
    # ---------------------------------------------------------------- #

    async def _handle_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_chat.id
        text    = update.message.text.strip()

        if chat_id not in _awaiting_gmail_code:
            return

        _awaiting_gmail_code.discard(chat_id)
        flow = _gmail_flows.pop(chat_id, None)

        if flow is None:
            await update.message.reply_text(
                "Session expired. Send /setupgmail to start again."
            )
            return

        try:
            flow.fetch_token(code=text)
            creds = flow.credentials
            with open(TOKEN_PATH, "w") as f:
                f.write(creds.to_json())
            await update.message.reply_text(
                "Gmail connected. Your next briefing will include your unread emails."
            )
        except Exception as e:
            logger.error(f"Gmail token exchange failed for {chat_id}: {e}")
            await update.message.reply_text(
                "That code didn't work. Send /setupgmail to try again."
            )

    # ---------------------------------------------------------------- #
    # Error handler                                                     #
    # ---------------------------------------------------------------- #

    async def _handle_error(self, update: object, context: ContextTypes.DEFAULT_TYPE):
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
        MAX_LEN = 4096
        chunks = [text[i:i + MAX_LEN] for i in range(0, len(text), MAX_LEN)]
        for chunk in chunks:
            await self._app.bot.send_message(chat_id=chat_id, text=chunk)
        logger.info(f"send_message: delivered to chat_id={chat_id}")

    async def send_message_with_keyboard(self, chat_id: int, text: str, keyboard: InlineKeyboardMarkup) -> None:
        await self._app.bot.send_message(
            chat_id=chat_id, text=text, reply_markup=keyboard
        )

    async def start_polling(self) -> None:
        logger.info("Telegram bot polling started")
        await self._app.initialize()
        await self._app.start()
        await self._app.updater.start_polling(drop_pending_updates=False)
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
