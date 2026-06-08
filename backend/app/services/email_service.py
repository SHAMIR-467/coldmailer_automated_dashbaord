import asyncio
import html
import logging
import smtplib
from datetime import date
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formatdate, make_msgid

from app.config import settings
from app.services.ollama_service import generate_cold_email

logger = logging.getLogger(__name__)
BOUNCE_KEYWORDS = ("user unknown", "mailbox not found", "550")


def is_bounce_error(error: Exception | str) -> bool:
    value = str(error).lower()
    return any(keyword in value for keyword in BOUNCE_KEYWORDS)


def build_html_email(subject: str, body: str, from_name: str) -> str:
    paragraphs = "".join(
        f'<p style="margin:0 0 16px 0;">{html.escape(part).replace(chr(10), "<br />")}</p>'
        for part in body.split("\n\n")
        if part.strip()
    )
    safe_from_name = html.escape(from_name or settings.SMTP_FROM_NAME or "Coldmailer")
    safe_subject = html.escape(subject)
    return f"""<!doctype html>
<html>
  <body style="margin:0;background:#f4f4f6;font-family:Arial,Helvetica,sans-serif;">
    <div style="max-width:600px;margin:0 auto;background:#ffffff;">
      <div style="background:#1a1a2e;color:#ffffff;padding:20px 24px;font-size:18px;font-weight:700;">
        {safe_from_name}
      </div>
      <div style="padding:24px;color:#333333;font-size:16px;line-height:1.6;">
        <h1 style="font-size:20px;line-height:1.3;margin:0 0 18px 0;color:#1a1a2e;">{safe_subject}</h1>
        {paragraphs}
      </div>
      <div style="background:#f0f1f4;color:#6b7280;padding:16px 24px;font-size:12px;line-height:1.5;">
        You received this email because your business contact information was publicly available. Reply unsubscribe to opt out.
      </div>
    </div>
  </body>
</html>"""


async def send_email(
    to_email: str,
    subject: str,
    body: str,
    from_name: str | None = None,
    from_email: str | None = None,
) -> bool:
    sender_name = from_name or settings.SMTP_FROM_NAME or "Coldmailer"
    sender_email = from_email or settings.SMTP_FROM_EMAIL
    if not to_email or not sender_email or not settings.SMTP_HOST:
        logger.error("Missing SMTP settings or recipient email")
        return False

    message = MIMEMultipart("alternative")
    message["From"] = f"{sender_name} <{sender_email}>"
    message["To"] = to_email
    message["Subject"] = subject
    message["Message-ID"] = make_msgid(domain=sender_email.split("@")[-1])
    message["Date"] = formatdate(localtime=True)
    message.attach(MIMEText(body, "plain", "utf-8"))
    message.attach(MIMEText(build_html_email(subject, body, sender_name), "html", "utf-8"))

    def _send() -> bool:
        try:
            if settings.SMTP_PORT == 465:
                smtp = smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT, timeout=30)
            else:
                smtp = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=30)
            with smtp:
                if settings.SMTP_PORT != 465:
                    smtp.starttls()
                if settings.SMTP_USER:
                    smtp.login(settings.SMTP_USER, settings.SMTP_PASS)
                smtp.sendmail(sender_email, [to_email], message.as_string())
            return True
        except Exception as exc:
            logger.exception("Failed to send email to %s: %s", to_email, exc)
            return False

    return await asyncio.to_thread(_send)


def check_daily_limit(redis_client) -> tuple[int, bool]:
    key = f"emails_sent:{date.today().isoformat()}"
    sent = int(redis_client.get(key) or 0)
    return sent, sent >= settings.DAILY_EMAIL_LIMIT


async def send_batch(leads: list, job_keyword: str, redis_client) -> dict[str, int]:
    sent = 0
    failed = 0
    skipped = 0
    for index, lead in enumerate(leads[:20]):
        emails_sent_today, at_limit = check_daily_limit(redis_client)
        if at_limit or not getattr(lead, "email", None):
            skipped += 1
            continue
        generated = await generate_cold_email(lead, job_keyword)
        if await send_email(lead.email, generated["subject"], generated["body"]):
            key = f"emails_sent:{date.today().isoformat()}"
            redis_client.incr(key)
            redis_client.expire(key, 86400)
            sent += 1
        else:
            failed += 1
        if index < len(leads[:20]) - 1:
            await asyncio.sleep(5)
    return {"sent": sent, "failed": failed, "skipped": skipped}


async def send_email_to_lead(lead, subject: str, body: str) -> bool:
    return await send_email(lead.email or "", subject, body)
