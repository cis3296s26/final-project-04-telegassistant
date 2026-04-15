# tests/test_bot.py
# ============================================================
# Unit tests for bot/telegram_client.py
#
# These tests do NOT connect to Telegram.
# The Application is mocked out so handlers can be tested in
# isolation — fast, offline, no token needed.
#
# Run with:  pytest tests/test_bot.py -v
# ============================================================
import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


# ---------------------------------------------------------------------------
# Fixtures & helpers
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def patch_application():
    """
    Patch telegram.ext.Application for every test in this module.
    This stops the constructor from trying to reach Telegram.
    """
    with patch("bot.telegram_client.Application") as mock_cls:
        mock_app = MagicMock()
        mock_cls.builder.return_value.token.return_value.build.return_value = mock_app
        yield mock_cls


def make_bot(db=None):
    """Return a TelegramBotClient with a fake token (and optional fake DB)."""
    from bot.telegram_client import TelegramBotClient
    return TelegramBotClient(token="test_token", db=db)


def make_update(chat_id=12345, first_name="Alex", username="alex_tg"):
    """Build a minimal fake Update object — only the fields our handlers touch."""
    update = MagicMock()
    update.effective_chat.id = chat_id
    update.effective_user.first_name = first_name
    update.effective_user.username = username
    update.message.reply_text = AsyncMock()
    return update


def run(coro):
    """Run a coroutine synchronously — keeps tests simple without pytest-asyncio."""
    return asyncio.run(coro)


# ---------------------------------------------------------------------------
# /start
# ---------------------------------------------------------------------------

class TestHandleStart:

    def test_sends_greeting_with_users_name(self):
        bot    = make_bot()
        update = make_update(first_name="Jordan")
        run(bot._handle_start(update, MagicMock()))
        update.message.reply_text.assert_called_once()
        reply = update.message.reply_text.call_args[0][0]
        assert "Jordan" in reply

    def test_registers_user_in_db(self):
        fake_db = MagicMock()
        bot     = make_bot(db=fake_db)
        update  = make_update(chat_id=99999, first_name="Jordan")
        run(bot._handle_start(update, MagicMock()))
        fake_db.register_user.assert_called_once_with(telegram_id=99999, name="Jordan")

    def test_still_replies_when_no_db_injected(self):
        """Bot works even before DB engineer wires their layer."""
        bot    = make_bot()   # no db
        update = make_update()
        run(bot._handle_start(update, MagicMock()))
        update.message.reply_text.assert_called_once()

    def test_still_replies_when_db_raises(self):
        """A broken DB must not leave the user with no response."""
        fake_db = MagicMock()
        fake_db.register_user.side_effect = Exception("DB unavailable")
        bot    = make_bot(db=fake_db)
        update = make_update()
        run(bot._handle_start(update, MagicMock()))   # should not raise
        update.message.reply_text.assert_called_once()

    def test_falls_back_to_username_when_no_first_name(self):
        update = make_update(first_name=None, username="mx_robot")
        bot    = make_bot()
        run(bot._handle_start(update, MagicMock()))
        reply = update.message.reply_text.call_args[0][0]
        assert "mx_robot" in reply


# ---------------------------------------------------------------------------
# /help
# ---------------------------------------------------------------------------

class TestHandleHelp:

    def test_returns_help_text_constant(self):
        from bot.telegram_client import HELP_TEXT
        bot    = make_bot()
        update = make_update()
        run(bot._handle_help(update, MagicMock()))
        update.message.reply_text.assert_called_once_with(HELP_TEXT)

    def test_help_text_mentions_all_commands(self):
        from bot.telegram_client import HELP_TEXT
        for cmd in ("/start", "/help", "/status"):
            assert cmd in HELP_TEXT, f"{cmd} missing from HELP_TEXT"


# ---------------------------------------------------------------------------
# /status
# ---------------------------------------------------------------------------

class TestHandleStatus:

    def test_says_online(self):
        bot    = make_bot()
        update = make_update()
        run(bot._handle_status(update, MagicMock()))
        reply = update.message.reply_text.call_args[0][0]
        assert "online" in reply.lower()


# ---------------------------------------------------------------------------
# send_message
# ---------------------------------------------------------------------------

class TestSendMessage:

    def test_calls_app_bot_send_message(self):
        bot = make_bot()
        bot._app.bot.send_message = AsyncMock()
        run(bot.send_message(chat_id=123, text="hello"))
        bot._app.bot.send_message.assert_called_once_with(
            chat_id=123,
            text="hello",
            parse_mode="Markdown",
        )

    def test_splits_message_over_4096_chars(self):
        bot  = make_bot()
        bot._app.bot.send_message = AsyncMock()
        long_text = "x" * 5000          # 5000 chars — needs two chunks
        run(bot.send_message(chat_id=1, text=long_text))
        assert bot._app.bot.send_message.call_count == 2

    def test_raises_on_telegram_failure(self):
        bot = make_bot()
        bot._app.bot.send_message = AsyncMock(side_effect=Exception("Network error"))
        with pytest.raises(Exception, match="Network error"):
            run(bot.send_message(chat_id=1, text="hi"))
