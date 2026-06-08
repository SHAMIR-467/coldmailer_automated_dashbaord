import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.google_maps import _extract_email_from_current_page, scrape_google_maps


def test_email_extraction_from_mailto_link():
    link = AsyncMock()
    link.get_attribute.return_value = "mailto:sales@example.com"
    page = MagicMock()
    page.locator.return_value.all = AsyncMock(return_value=[link])
    assert asyncio.run(_extract_email_from_current_page(page)) == "sales@example.com"


def test_scrape_handles_empty_results_gracefully():
    with patch("app.services.google_maps.async_playwright", side_effect=TimeoutError("blocked")):
        assert asyncio.run(scrape_google_maps("restaurant", "Austin", 1)) == []


def test_scrape_handles_network_timeout_gracefully():
    with patch("app.services.google_maps.async_playwright", side_effect=TimeoutError("timeout")):
        assert asyncio.run(scrape_google_maps("dentist", "Dallas", 1)) == []


def test_scrape_returns_list_structure_on_failure_path():
    with patch("app.services.google_maps.async_playwright", side_effect=RuntimeError("no browser")):
        result = asyncio.run(scrape_google_maps("plumber", "Denver", 1))
        assert isinstance(result, list)
