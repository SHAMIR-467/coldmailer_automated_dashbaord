import asyncio

import httpx
import respx

from app.config import settings
from app.services.ollama_service import generate_cold_email


class Lead:
    business_name = "Acme Dental"
    category = "dentist"
    city = "Austin"


@respx.mock
def test_generates_email_with_json_structure():
    respx.post(f"{settings.OLLAMA_BASE_URL}/api/generate").mock(
        return_value=httpx.Response(200, json={"response": '{"subject":"Austin dental growth","body":"Hello\\n\\nValue\\n\\nCTA"}'})
    )
    result = asyncio.run(generate_cold_email(Lead(), "dentistry"))
    assert set(result) == {"subject", "body"}
    assert result["subject"] == "Austin dental growth"


@respx.mock
def test_malformed_json_falls_back():
    respx.post(f"{settings.OLLAMA_BASE_URL}/api/generate").mock(return_value=httpx.Response(200, json={"response": "not json"}))
    result = asyncio.run(generate_cold_email(Lead(), "dentistry"))
    assert "Acme Dental" in result["body"]


@respx.mock
def test_connection_refused_raises_descriptive_error():
    respx.post(f"{settings.OLLAMA_BASE_URL}/api/generate").mock(side_effect=httpx.ConnectError("refused"))
    try:
        asyncio.run(generate_cold_email(Lead(), "dentistry"))
    except RuntimeError as exc:
        assert "Ollama connection failed" in str(exc)
