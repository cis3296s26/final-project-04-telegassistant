# ai/llm_client.py
# ============================================================
# TeleGAssistant — LLM Client
# Owned by: AI Engineer
#
# Implements AbstractAI using a local ollama inference server.
# Expects ollama to be running on localhost:11434 with gemma2:2b pulled.
# ============================================================

import httpx
from interfaces import AbstractAI

OLLAMA_BASE = "http://localhost:11434"
MODEL = "gemma2:2b"

SYSTEM_PROMPT = (
    "You are a no-nonsense daily briefing assistant. "
    "Output a clean, structured morning briefing using only the data provided. "
    "Rules: "
    "1. No emojis. "
    "2. No motivational language, encouragement, or filler phrases. "
    "3. No invented content — only use what is explicitly given. "
    "4. If a section has no items, skip it entirely — do not comment on it. "
    "5. Use this exact structure, only including sections that have data: "
    "   Good morning, [name]. Here is your briefing for [day]. "
    "   (blank line) "
    "   Events: "
    "   - [time] [title] "
    "   (blank line) "
    "   Tasks: "
    "   - [due date] [title] ([status]) "
    "   (blank line) "
    "   Deadlines: "
    "   - [title] — due [urgency] "
    "6. Maximum 20 lines. No sign-off."
)


class LLMClient(AbstractAI):

    def __init__(self, base_url: str = OLLAMA_BASE, model: str = MODEL):
        self.base_url = base_url
        self.model = model

    async def generate_briefing(self, context: str) -> str:
        """
        Sends context to Gemma 2B and returns a Telegram-ready briefing string.
        Raises on any failure so the caller can trigger the fallback briefing.
        """
        async with httpx.AsyncClient(timeout=90.0) as client:
            response = await client.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "system": SYSTEM_PROMPT,
                    "prompt": context,
                    "stream": False,
                },
            )
            response.raise_for_status()
            return response.json()["response"]

    async def health_check(self) -> bool:
        """
        Returns True if the ollama server is reachable and gemma2:2b is available.
        Also warms up the model so the first briefing doesn't cold-start.
        Never raises — always returns bool.
        """
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                r = await client.get(f"{self.base_url}/api/tags")
                if r.status_code != 200:
                    return False
                models = [m["name"] for m in r.json().get("models", [])]
                if self.model not in models:
                    return False

            # Warm up — loads model weights into memory before first briefing
            async with httpx.AsyncClient(timeout=90.0) as client:
                await client.post(
                    f"{self.base_url}/api/generate",
                    json={"model": self.model, "prompt": "hi", "stream": False},
                )
            return True
        except Exception:
            return False
