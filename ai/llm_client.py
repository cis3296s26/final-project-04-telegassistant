import os

import httpx

from interfaces import AbstractAI


class LLMClient(AbstractAI):
    def __init__(self, base_url=None, model=None, timeout=20.0):
        self._base_url = (base_url or os.getenv("LLM_BASE_URL", "http://localhost:11434")).rstrip("/")
        self._model = model or os.getenv("LLM_MODEL", "gemma2:2b")
        self._timeout = timeout

    async def generate_briefing(self, context: str) -> str:
        payload = {
            "model": self._model,
            "prompt": context,
            "stream": False,
        }
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.post(f"{self._base_url}/api/generate", json=payload)
                response.raise_for_status()
                data = response.json()
        except Exception as exc:
            raise RuntimeError(f"LLM request failed: {exc}") from exc

        text = data.get("response", "").strip()
        if not text:
            raise RuntimeError("LLM returned empty response")
        return text

    async def health_check(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self._base_url}/api/tags")
                response.raise_for_status()
            return True
        except Exception:
            return False
