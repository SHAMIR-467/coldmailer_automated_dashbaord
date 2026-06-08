import asyncio
import logging
import random
import re
from urllib.parse import quote_plus, urljoin

from playwright.async_api import BrowserContext, async_playwright

from app.config import settings
from app.database import get_redis

logger = logging.getLogger(__name__)
scraper_logger = logging.getLogger("scraper")

EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/125.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_5) AppleWebKit/605.1.15 Version/16.6 Safari/605.1.15",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4) AppleWebKit/537.36 Chrome/125.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:126.0) Gecko/20100101 Firefox/126.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14.4; rv:126.0) Gecko/20100101 Firefox/126.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Edg/125.0 Safari/537.36",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:126.0) Gecko/20100101 Firefox/126.0",
    "Mozilla/5.0 (Windows NT 10.0; ARM64) AppleWebKit/537.36 Chrome/125.0 Safari/537.36",
]
VIEWPORTS = [(1366, 768), (1440, 900), (1536, 864), (1600, 900), (1920, 1080), (1280, 800)]


def _first_email(text: str) -> str | None:
    matches = EMAIL_RE.findall(text or "")
    for match in matches:
        email = match.strip().strip(".,;:()[]{}<>").lower()
        if not email.endswith((".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg")):
            return email
    return None


async def extract_email_from_website(website_url: str, context: BrowserContext) -> str | None:
    page = await context.new_page()
    try:
        await page.goto(website_url, wait_until="domcontentloaded", timeout=8000)
        email = await _extract_email_from_current_page(page)
        if email:
            return email

        contact_url = urljoin(website_url.rstrip("/") + "/", "contact")
        await page.goto(contact_url, wait_until="domcontentloaded", timeout=8000)
        return await _extract_email_from_current_page(page)
    except Exception as exc:
        logger.info("Email extraction failed for %s: %s", website_url, exc)
        return None
    finally:
        await page.close()


async def _extract_email_from_current_page(page) -> str | None:
    try:
        mailto_links = await page.locator('a[href^="mailto:"]').all()
        for link in mailto_links:
            href = await link.get_attribute("href")
            if href:
                email = href.replace("mailto:", "").split("?")[0].strip()
                if EMAIL_RE.fullmatch(email):
                    return email.lower()
        content = await page.content()
        return _first_email(content)
    except Exception as exc:
        logger.info("Email extraction from current page failed: %s", exc)
        return None


async def get_business_details(maps_url: str, context: BrowserContext) -> dict:
    page = await context.new_page()
    try:
        await page.goto(maps_url, wait_until="domcontentloaded", timeout=15000)
        await page.wait_for_timeout(1500)
        return await page.evaluate(
            """
            () => {
              const textOf = (selector) => document.querySelector(selector)?.textContent?.trim() || null;
              const ariaOf = (selector) => document.querySelector(selector)?.getAttribute('aria-label') || null;
              const address = ariaOf('button[data-item-id="address"]') || textOf('button[data-item-id="address"]');
              const category = document.querySelector('button[jsaction*="category"]')?.textContent?.trim()
                || document.querySelector('[aria-label*="Category"]')?.textContent?.trim()
                || null;
              const phone = ariaOf('button[data-item-id^="phone"]') || textOf('button[data-item-id^="phone"]');
              return { address, category, phone };
            }
            """
        )
    except Exception as exc:
        logger.info("Business detail enrichment failed for %s: %s", maps_url, exc)
        return {}
    finally:
        await page.close()


async def scrape_google_maps(keyword: str, city: str, batch_size: int = 20) -> list[dict]:
    try:
        redis = get_redis()
        cooldown_key = "google_maps:captcha_cooldown"
        if await redis.get(cooldown_key):
            scraper_logger.warning("Google Maps scrape skipped due to captcha cooldown", extra={"extra": {"keyword": keyword, "city": city}})
            return []
        async with async_playwright() as p:
            launch_options: dict[str, object] = {"headless": True, "args": ["--no-sandbox"]}
            if settings.PROXY_URL:
                launch_options["proxy"] = {"server": settings.PROXY_URL}
            browser = await p.chromium.launch(**launch_options)
            width, height = random.choice(VIEWPORTS)
            context = await browser.new_context(
                user_agent=random.choice(USER_AGENTS),
                viewport={"width": width, "height": height},
                locale="en-US",
                timezone_id="America/New_York",
            )
            page = await context.new_page()
            try:
                url = f"https://www.google.com/maps/search/{quote_plus(keyword)}+{quote_plus(city)}"
                scraper_logger.info("Starting city scrape", extra={"extra": {"keyword": keyword, "city": city}})
                await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                await page.wait_for_timeout(random.randint(1000, 2500))
                page_text = (await page.locator("body").inner_text(timeout=5000)).lower()
                if "unusual traffic" in page_text or "our systems have detected" in page_text:
                    await redis.setex(cooldown_key, 300, "1")
                    scraper_logger.warning("Captcha detected, cooldown set", extra={"extra": {"keyword": keyword, "city": city}})
                    return []
                await page.wait_for_selector('div[role="feed"]', timeout=15000)

                feed = page.locator('div[role="feed"]')
                leads: list[dict] = []
                seen: set[str] = set()
                stagnant_rounds = 0

                while len(leads) < batch_size and stagnant_rounds < 5:
                    result_elements = page.locator('div[role="feed"] > div')
                    count = await result_elements.count()
                    before_count = len(leads)

                    for index in range(count):
                        if len(leads) >= batch_size:
                            break

                        element = result_elements.nth(index)
                        extracted = await element.evaluate(
                            """
                            (node) => {
                              const text = node.innerText || "";
                              const lines = text.split("\\n").map((v) => v.trim()).filter(Boolean);
                              const link = node.querySelector('a[href*="/maps/place/"]');
                              const website = Array.from(node.querySelectorAll('a[href]')).find((a) => {
                                const href = a.href || "";
                                return href.startsWith("http") && !href.includes("google.") && !href.includes("/maps/");
                              });
                              const phoneMatch = text.match(/(\\+?\\d[\\d\\s().-]{7,}\\d)/);
                              const ratingMatch = text.match(/([1-5]\\.\\d)/);
                              const reviewsMatch = text.match(/\\(([\\d,]+)\\)/);
                              return {
                                name: link?.getAttribute("aria-label") || lines[0] || null,
                                address: lines.find((line) => /\\d+\\s+/.test(line)) || null,
                                phone: phoneMatch ? phoneMatch[1] : null,
                                rating: ratingMatch ? Number(ratingMatch[1]) : null,
                                reviews: reviewsMatch ? Number(reviewsMatch[1].replace(/,/g, "")) : null,
                                website_url: website?.href || null,
                                maps_url: link?.href || null
                              };
                            }
                            """
                        )

                        name = (extracted.get("name") or "").strip()
                        maps_url = extracted.get("maps_url")
                        dedupe_key = maps_url or f"{name}:{city}"
                        if not name or dedupe_key in seen:
                            continue
                        seen.add(dedupe_key)

                        if maps_url and (not extracted.get("address") or not extracted.get("phone")):
                            details = await get_business_details(maps_url, context)
                            extracted.update({key: value for key, value in details.items() if value and not extracted.get(key)})

                        email = None
                        website_url = extracted.get("website_url")
                        if website_url:
                            email = await extract_email_from_website(website_url, context)
                            await asyncio.sleep(random.uniform(2, 5))

                        leads.append(
                            {
                                "business_name": name[:500],
                                "email": email,
                                "phone": extracted.get("phone"),
                                "address": extracted.get("address"),
                                "website": website_url,
                                "category": extracted.get("category"),
                                "city": city,
                                "rating": extracted.get("rating"),
                                "review_count": extracted.get("reviews"),
                                "maps_url": maps_url,
                            }
                        )

                        if len(leads) % 5 == 0:
                            await feed.evaluate("(el) => el.scrollBy(0, 500)")
                            await page.wait_for_timeout(random.randint(800, 1800))

                    if len(leads) == before_count:
                        stagnant_rounds += 1
                    else:
                        stagnant_rounds = 0
                    await feed.evaluate("(el) => el.scrollBy(0, 500)")
                    await page.wait_for_timeout(random.randint(800, 1800))

                deduped: list[dict] = []
                seen_pairs: set[str] = set()
                for lead in leads:
                    key = f"{lead['business_name'].strip().lower()}:{lead['city'].strip().lower()}"
                    if key in seen_pairs:
                        continue
                    seen_pairs.add(key)
                    deduped.append(lead)
                scraper_logger.info("Finished city scrape", extra={"extra": {"keyword": keyword, "city": city, "lead_count": len(deduped)}})
                return deduped[:batch_size]
            finally:
                await context.close()
                await browser.close()
    except Exception as exc:
        logger.exception("Google Maps scrape failed for keyword=%s city=%s: %s", keyword, city, exc)
        return []
