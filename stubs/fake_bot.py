# stubs/fake_bot.py
import asyncio
from interfaces import AbstractBot


class FakeBot(AbstractBot):
    """
    Fake Telegram bot. Prints messages to terminal instead of sending them.
    Replace with real TelegramBotClient once Bot Engineer is ready.
    """

    async def send_message(self, chat_id: int, text: str) -> None:
        border = "=" * 55
        print(f"\n{border}")
        print(f"  📨 TELEGRAM MESSAGE → chat_id: {chat_id}")
        print(border)
        print(text)
        print(f"{border}\n")

    async def start_polling(self) -> None:
        print("[FakeBot] Polling started (fake — not actually connected to Telegram)")
        while True:
            await asyncio.sleep(60)