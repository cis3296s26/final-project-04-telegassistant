# stubs/fake_ai.py
from interfaces import AbstractAI


class FakeAI(AbstractAI):
    """
    Fake AI client. Echoes back the context so you can verify
    your briefing pipeline is building prompts correctly.
    Replace with real LLMClient once AI Engineer is ready.
    """

    async def generate_briefing(self, context: str) -> str:
        # Shows you exactly what context your pipeline is sending
        preview = context[:300] + "..." if len(context) > 300 else context
        return (
            f"🤖 *[STUB BRIEFING — AI not connected yet]*\n\n"
            f"Context received by AI:\n"
            f"```\n{preview}\n```"
        )

    async def health_check(self) -> bool:
        print("[FakeAI] health_check() called → returning True")
        return True