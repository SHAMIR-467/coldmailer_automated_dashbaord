import json
import logging

import httpx
from sqlalchemy import select

from app.config import settings
from app.database import AsyncSessionLocal
from app.models import CityKeyword

logger = logging.getLogger(__name__)

FALLBACK_CITIES = [
    "New York",
    "Los Angeles",
    "Chicago",
    "Houston",
    "Phoenix",
    "Philadelphia",
    "San Antonio",
    "San Diego",
    "Dallas",
    "San Jose",
    "Austin",
    "Jacksonville",
    "Fort Worth",
    "Columbus",
    "Charlotte",
    "San Francisco",
    "Indianapolis",
    "Seattle",
    "Denver",
    "Washington",
]


async def generate_cities_for_keyword(keyword: str) -> list[str]:
    normalized_keyword = keyword.strip().lower()
    if not normalized_keyword:
        return FALLBACK_CITIES

    async with AsyncSessionLocal() as db:
        cached = await db.scalar(select(CityKeyword).where(CityKeyword.keyword == normalized_keyword))
        if cached:
            return list(cached.cities)

    try:
        prompt = f"""You are a geographic research assistant.
List 40 major cities where businesses related to '{keyword}' commonly operate.
Consider population density and business activity.
Return ONLY a valid JSON array of city name strings.
Example format: ["Lahore", "Karachi", "Islamabad"]
No explanation, no markdown, just the JSON array."""
        async with httpx.AsyncClient(base_url=settings.OLLAMA_BASE_URL, timeout=60) as client:
            response = await client.post(
                "/api/generate",
                json={"model": settings.OLLAMA_MODEL, "prompt": prompt, "stream": False},
            )
            response.raise_for_status()
            raw_text = response.json().get("response", "")

        parsed = json.loads(raw_text)
        cities = [str(city).strip() for city in parsed if str(city).strip()]
        if not cities:
            raise ValueError("Ollama returned an empty city list")

        async with AsyncSessionLocal() as db:
            db.add(CityKeyword(keyword=normalized_keyword, cities=cities))
            await db.commit()
        return cities
    except Exception as exc:
        logger.warning("Falling back to default cities for %s: %s", keyword, exc)
        return FALLBACK_CITIES
