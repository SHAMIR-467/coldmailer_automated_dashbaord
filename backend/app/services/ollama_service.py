import json
import re

import httpx

from app.config import settings


def _fallback_email(lead, keyword: str) -> dict[str, str]:
    subject = f"Helping {lead.business_name} grow locally"[:55]
    body = (
        f"Hi {lead.business_name},\n\n"
        f"I noticed your {lead.category or 'local business'} in {lead.city} and thought services related to "
        f"{keyword} could help you reach more nearby customers.\n\n"
        "Would you be open to a 15-minute call this week?\n\n"
        "Warm regards,\n"
        f"The {keyword.title()} Team"
    )
    return {"subject": subject, "body": body}


def _strip_json_fences(value: str) -> str:
    cleaned = value.strip()
    cleaned = re.sub(r"^```(?:json)?", "", cleaned, flags=re.IGNORECASE).strip()
    cleaned = re.sub(r"```$", "", cleaned).strip()
    return cleaned


async def generate_cold_email(lead, keyword: str) -> dict[str, str]:
    prompt = f"""You are a professional B2B cold email copywriter.

Write a personalized cold outreach email for this business:
- Business Name: {lead.business_name}
- Category: {lead.category or 'local business'}
- City: {lead.city}
- Our Offering: Services related to {keyword}

STRICT RULES:
1. Subject line: max 55 characters, no generic phrases like "Quick question"
2. Opening: reference their specific city or category naturally
3. Body: exactly 3 short paragraphs, total under 120 words
4. Value prop: be specific to their business type
5. CTA: one soft ask - "open to a 15-minute call this week?"
6. Sign-off: use "Warm regards," then "The {keyword.title()} Team"
7. NO placeholders, NO brackets, NO ALL CAPS

Return ONLY this exact JSON (no markdown, no explanation):
{{"subject": "your subject here", "body": "full email body here"}}"""
    try:
        async with httpx.AsyncClient(base_url=settings.OLLAMA_BASE_URL, timeout=60) as client:
            response = await client.post(
                "/api/generate",
                json={
                    "model": settings.OLLAMA_MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.7, "num_predict": 400},
                },
            )
            response.raise_for_status()
            raw = _strip_json_fences(response.json().get("response", ""))
    except httpx.RequestError as exc:
        raise RuntimeError(f"Ollama connection failed at {settings.OLLAMA_BASE_URL}: {exc}") from exc

    try:
        parsed = json.loads(raw)
        subject = str(parsed["subject"]).strip()[:55]
        body = str(parsed["body"]).strip()
        if not subject or not body:
            raise ValueError("Ollama JSON missing subject/body")
        return {"subject": subject, "body": body}
    except Exception:
        return _fallback_email(lead, keyword)


async def generate_email_for_lead(lead) -> tuple[str, str]:
    generated = await generate_cold_email(lead, lead.category or "your business")
    return generated["subject"], generated["body"]


async def test_ollama_connection() -> bool:
    try:
        async with httpx.AsyncClient(base_url=settings.OLLAMA_BASE_URL, timeout=5) as client:
            response = await client.get("/api/tags")
            return response.status_code == 200
    except httpx.RequestError:
        return False
