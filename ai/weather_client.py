# ai/weather_client.py
# ============================================================
# TeleGAssistant — Weather Client
# Owned by: AI Engineer
#
# Fetches current conditions and today's forecast from
# OpenWeatherMap. Returns None gracefully on any failure
# so the briefing pipeline skips the weather section silently.
# ============================================================

import os
import httpx

WEATHER_BASE = "https://api.openweathermap.org/data/2.5/weather"
DEFAULT_CITY = "Philadelphia,PA,US"


async def get_weather(city: str = DEFAULT_CITY) -> dict | None:
    api_key = os.getenv("WEATHER_API_KEY")
    if not api_key:
        return None

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.get(WEATHER_BASE, params={
                "q":     city,
                "appid": api_key,
                "units": "imperial",
            })
            r.raise_for_status()
            data = r.json()

        return {
            "city":      data["name"],
            "temp":      round(data["main"]["temp"]),
            "high":      round(data["main"]["temp_max"]),
            "low":       round(data["main"]["temp_min"]),
            "condition": data["weather"][0]["description"].capitalize(),
        }
    except Exception:
        return None
