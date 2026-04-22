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
    "You are a morning briefing assistant. "
    "Your only job is to reformat the data given to you into the exact layout specified in the prompt. "
    "Rules: "
    "1. Only use data explicitly provided — never invent, guess, or add anything. "
    "2. Reproduce every item given. Do not summarize, skip, or truncate any items. "
    "3. Follow the format and emoji structure shown in the prompt exactly. "
    "4. Keep blank lines between sections. "
    "5. No sign-off, no motivational filler, no commentary."
)


class LLMClient(AbstractAI):

    def __init__(self, base_url: str = OLLAMA_BASE, model: str = MODEL):
        self.base_url = base_url
        self.model = model

    async def generate_briefing(self, context: str) -> str:
        async with httpx.AsyncClient(timeout=90.0) as client:
            response = await client.post(
                f"{self.base_url}/api/generate",
                json={
                    "model":  self.model,
                    "system": SYSTEM_PROMPT,
                    "prompt": context,
                    "stream": False,
                },
            )
            response.raise_for_status()
            return response.json()["response"]

    async def triage_emails(self, emails: list[dict]) -> str:
        if not emails:
            return "No unread emails."

        lines = ["Here are the unread emails to triage:\n"]
        for i, e in enumerate(emails, 1):
            lines.append(f"{i}. From: {e['from']}")
            lines.append(f"   Subject: {e['subject']}")
            if e.get("snippet"):
                lines.append(f"   Preview: {e['snippet']}")
            lines.append("")

        prompt = "\n".join(lines)
        prompt += (
            "\nFrom the above, identify only the emails that are actionable or important "
            "(replies needed, deadlines, alerts, work/school communications). "
            "Filter out newsletters, promotions, automated notifications, and spam. "
            "Return a clean numbered list sorted by urgency using this exact format:\n\n"
            "[number]. [Sender name]\n"
            "   [Subject line — keep it concise]\n"
            "   [Action needed / FYI]: [one sentence on why it matters]\n\n"
            "No bold, no asterisks, no markdown. Plain text only. "
            "If none are important, say: No actionable emails found."
        )

        async with httpx.AsyncClient(timeout=90.0) as client:
            response = await client.post(
                f"{self.base_url}/api/generate",
                json={
                    "model":  self.model,
                    "system": "You are an email triage assistant. Filter and rank emails by importance. Be concise and direct.",
                    "prompt": prompt,
                    "stream": False,
                },
            )
            response.raise_for_status()
            return response.json()["response"]

    async def health_check(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                r = await client.get(f"{self.base_url}/api/tags")
                if r.status_code != 200:
                    return False
                models = [m["name"] for m in r.json().get("models", [])]
                if self.model not in models:
                    return False

            async with httpx.AsyncClient(timeout=90.0) as client:
                await client.post(
                    f"{self.base_url}/api/generate",
                    json={"model": self.model, "prompt": "hi", "stream": False},
                )
            return True
        except Exception:
            return False
