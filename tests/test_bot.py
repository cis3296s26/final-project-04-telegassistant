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


def make_bot(db=None, ai=None):
    """Return a TelegramBotClient with a fake token."""
    from bot.telegram_client import TelegramBotClient
    return TelegramBotClient(token="test_token", db=db, ai=ai)


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
# escape_md2 utility
# ---------------------------------------------------------------------------

class TestEscapeMd2:

    def test_escapes_dot_and_exclamation(self):
        from bot.telegram_client import escape_md2
        assert escape_md2("Hello!") == r"Hello\!"
        assert escape_md2("end.") == r"end\."

    def test_escapes_parens_and_brackets(self):
        from bot.telegram_client import escape_md2
        assert escape_md2("(ok)") == r"\(ok\)"
        assert escape_md2("[link]") == r"\[link\]"

    def test_plain_text_unchanged(self):
        from bot.telegram_client import escape_md2
        assert escape_md2("hello world") == "hello world"

    def test_emoji_unchanged(self):
        from bot.telegram_client import escape_md2
        assert escape_md2("☀️ good morning") == "☀️ good morning"

    def test_hyphen_escaped(self):
        from bot.telegram_client import escape_md2
        assert escape_md2("to-do") == r"to\-do"


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
        bot    = make_bot()
        update = make_update()
        run(bot._handle_start(update, MagicMock()))
        update.message.reply_text.assert_called_once()

    def test_still_replies_when_db_raises(self):
        """A broken DB must not leave the user with no response."""
        fake_db = MagicMock()
        fake_db.register_user.side_effect = Exception("DB unavailable")
        bot    = make_bot(db=fake_db)
        update = make_update()
        run(bot._handle_start(update, MagicMock()))
        update.message.reply_text.assert_called_once()

    def test_falls_back_to_username_when_no_first_name(self):
        from bot.telegram_client import escape_md2
        update = make_update(first_name=None, username="mx_robot")
        bot    = make_bot()
        run(bot._handle_start(update, MagicMock()))
        reply = update.message.reply_text.call_args[0][0]
        assert escape_md2("mx_robot") in reply

    def test_uses_markdownv2(self):
        bot    = make_bot()
        update = make_update()
        run(bot._handle_start(update, MagicMock()))
        kwargs = update.message.reply_text.call_args[1]
        assert kwargs.get("parse_mode") == "MarkdownV2"


# ---------------------------------------------------------------------------
# /help
# ---------------------------------------------------------------------------

class TestHandleHelp:

    def test_returns_help_text_constant(self):
        from bot.telegram_client import HELP_TEXT
        bot    = make_bot()
        update = make_update()
        run(bot._handle_help(update, MagicMock()))
        args, kwargs = update.message.reply_text.call_args
        assert args[0] == HELP_TEXT
        assert kwargs.get("parse_mode") == "MarkdownV2"

    def test_help_text_mentions_all_commands(self):
        from bot.telegram_client import HELP_TEXT
        for cmd in ("/start", "/help", "/status", "/briefing"):
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

    def test_uses_markdownv2(self):
        bot    = make_bot()
        update = make_update()
        run(bot._handle_status(update, MagicMock()))
        kwargs = update.message.reply_text.call_args[1]
        assert kwargs.get("parse_mode") == "MarkdownV2"


# ---------------------------------------------------------------------------
# /briefing
# ---------------------------------------------------------------------------

class TestHandleBriefing:

    def _make_db(self, chat_id=12345):
        """FakeDB that returns a single user matching chat_id."""
        db = MagicMock()
        db.get_active_users.return_value = [
            {"id": 1, "telegram_id": chat_id, "name": "Alex"}
        ]
        return db

    def test_sends_generating_message_then_briefing(self):
        fake_db = self._make_db()
        fake_ai = MagicMock()
        bot     = make_bot(db=fake_db, ai=fake_ai)
        update  = make_update(chat_id=12345)

        with patch("jobs.briefing.send_briefing_for_user", new=AsyncMock()) as mock_send:
            run(bot._handle_briefing(update, MagicMock()))

        # First reply is the "Generating..." ack
        first_reply = update.message.reply_text.call_args_list[0][0][0]
        assert "generating" in first_reply.lower() or "briefing" in first_reply.lower()
        # send_briefing_for_user was called with the right user
        mock_send.assert_called_once()

    def test_error_if_no_db(self):
        bot    = make_bot(ai=MagicMock())   # no db
        update = make_update()
        run(bot._handle_briefing(update, MagicMock()))
        reply = update.message.reply_text.call_args[0][0]
        assert "not" in reply.lower() or "unavailable" in reply.lower()

    def test_error_if_no_ai(self):
        bot    = make_bot(db=MagicMock())   # no ai
        update = make_update()
        run(bot._handle_briefing(update, MagicMock()))
        reply = update.message.reply_text.call_args[0][0]
        assert "not" in reply.lower() or "unavailable" in reply.lower()

    def test_error_if_user_not_registered(self):
        db = MagicMock()
        db.get_active_users.return_value = []   # no users
        bot    = make_bot(db=db, ai=MagicMock())
        update = make_update(chat_id=99999)
        run(bot._handle_briefing(update, MagicMock()))
        reply = update.message.reply_text.call_args[0][0]
        assert "not registered" in reply.lower() or "start" in reply.lower()

    def test_error_if_db_raises(self):
        db = MagicMock()
        db.get_active_users.side_effect = Exception("DB down")
        bot    = make_bot(db=db, ai=MagicMock())
        update = make_update()
        run(bot._handle_briefing(update, MagicMock()))
        reply = update.message.reply_text.call_args[0][0]
        assert "database" in reply.lower() or "try again" in reply.lower()

    def test_error_if_briefing_pipeline_raises(self):
        fake_db = self._make_db()
        bot     = make_bot(db=fake_db, ai=MagicMock())
        update  = make_update(chat_id=12345)

        with patch("jobs.briefing.send_briefing_for_user",
                   new=AsyncMock(side_effect=Exception("LLM timeout"))):
            run(bot._handle_briefing(update, MagicMock()))

        last_reply = update.message.reply_text.call_args_list[-1][0][0]
        assert "went wrong" in last_reply.lower() or "try again" in last_reply.lower()


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
        )

    def test_no_parse_mode_for_safe_plain_text_delivery(self):
        """send_message must not use any parse_mode — content is unpredictable."""
        bot = make_bot()
        bot._app.bot.send_message = AsyncMock()
        run(bot.send_message(chat_id=1, text="☀️ Good morning! (test)"))
        call_kwargs = bot._app.bot.send_message.call_args[1]
        assert "parse_mode" not in call_kwargs

    def test_splits_message_over_4096_chars(self):
        bot  = make_bot()
        bot._app.bot.send_message = AsyncMock()
        long_text = "x" * 5000
        run(bot.send_message(chat_id=1, text=long_text))
        assert bot._app.bot.send_message.call_count == 2

    def test_raises_on_telegram_failure(self):
        bot = make_bot()
        bot._app.bot.send_message = AsyncMock(side_effect=Exception("Network error"))
        with pytest.raises(Exception, match="Network error"):
            run(bot.send_message(chat_id=1, text="hi"))


# ---------------------------------------------------------------------------
# Global error handler
# ---------------------------------------------------------------------------

class TestHandleError:

    def test_replies_when_update_has_message(self):
        bot    = make_bot()
        update = make_update()
        # effective_message is the same as message in our fake Update
        update.effective_message = update.message

        context = MagicMock()
        context.error = Exception("boom")
        run(bot._handle_error(update, context))
        update.effective_message.reply_text.assert_called_once()
        reply = update.effective_message.reply_text.call_args[0][0]
        assert "went wrong" in reply.lower() or "try again" in reply.lower()
