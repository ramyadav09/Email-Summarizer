"""Gmail API service — fetching, reading, and sending emails."""

import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from bs4 import BeautifulSoup

from app.core.config import settings
from sqlalchemy.orm import Session
from app.core.logging import get_logger
from fastapi import Depends

from app.services.email_repository import save_email_snippets
logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _decode_body(data: str) -> str:
    """Decode base64url-encoded email body data."""
    return base64.urlsafe_b64decode(data + "==").decode("utf-8", errors="ignore")


def _extract_part_by_type(payload: dict, mime_type: str) -> str:
    """Recursively walk MIME parts to find a specific mime type."""
    if payload.get("mimeType") == mime_type and payload.get("body", {}).get("data"):
        return _decode_body(payload["body"]["data"])

    for part in payload.get("parts", []):
        result = _extract_part_by_type(part, mime_type)
        if result:
            return result
    return ""


def _build_service(token: str):
    """Build an authenticated Gmail API service client."""
    creds = Credentials(token=token)
    return build("gmail", "v1", credentials=creds)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def fetch_emails(
    token: str,
    db: Session,
    after: str | None = None,
    before: str | None = None,
    read_status: str | None = None,
) -> list[dict]:
    """Fetch a list of emails from Gmail filtered by domain and date range."""
    service = _build_service(token)

    domains = " OR ".join(f"from:(*@{d})" for d in settings.ALLOWED_DOMAINS)
    query = f"({domains})"
    if after:
        query += f" after:{after}"
    if before:
        query += f" before:{before}"
    if read_status:
        query += f" is:{read_status}"

    logger.info("Fetching emails with query: %s", query)

    results = (
        service.users().messages().list(userId="me", q=query, maxResults=20).execute()
    )
    messages = results.get("messages", [])  # ids and threadIds
    logger.info("Found %d messages", len(messages))

    emails = []
    for msg in messages:
        detail = (
            service.users()
            .messages()
            .get(
                userId="me",
                id=msg["id"],
                format="metadata",
                metadataHeaders=["From", "Subject"],
            )
            .execute()
        )   #msg details with snippet
        headers = {h["name"]: h["value"] for h in detail["payload"]["headers"]}
        label_ids = detail.get("labelIds", [])
        record={
                "id": msg["id"],
                "from": headers.get("From", ""),
                "subject": headers.get("Subject", ""),
                "snippet": detail.get("snippet", ""),
                "summary": None,
                "is_read": "UNREAD" not in label_ids,
            }
        emails.append(record)

    save_email_snippets(db, emails)
    return emails


def fetch_email_detail(token: str, email_id: str) -> dict:
    """Fetch the full detail of a single email and mark it as read."""
    service = _build_service(token)

    logger.debug("Fetching detail for email_id=%s", email_id)

    detail = (
        service.users()
        .messages()
        .get(userId="me", id=email_id, format="full")
        .execute()
    )
    payload = detail.get("payload", {})
    headers = {h["name"]: h["value"] for h in payload.get("headers", [])}

    # Extract plain text and html bodies
    body_plain = _extract_part_by_type(payload, "text/plain")
    body_html = _extract_part_by_type(payload, "text/html")

    # Fallback: if neither found, use snippet
    if not body_plain and not body_html:
        body_plain = detail.get("snippet", "")

    # Extract labels and mark as read
    labels = detail.get("labelIds", [])
    is_read = "UNREAD" not in labels

    if not is_read:
        try:
            _mark_as_read(service, email_id)
        except Exception:
            logger.warning(
                "Failed to mark email_id=%s as read", email_id, exc_info=True
            )

    return {
        "id": email_id,
        "thread_id": detail.get("threadId", ""),
        "from": headers.get("From", ""),
        "to": headers.get("To", ""),
        "subject": headers.get("Subject", ""),
        "snippet": detail.get("snippet", ""),
        "body": body_plain,
        "body_html": body_html,
        "date": headers.get("Date", ""),
        "message_id": headers.get("Message-ID", headers.get("Message-Id", "")),
        "labels": labels,
        "is_read": True,  # always true after viewing
    }


def send_reply(
    token: str,
    thread_id: str,
    to: str,
    subject: str,
    body: str,
    original_message_id: str | None = None,
) -> dict:
    """Send a reply email within the same Gmail thread."""
    service = _build_service(token)

    msg = MIMEMultipart("alternative")
    msg["To"] = to
    msg["Subject"] = subject if subject.lower().startswith("re:") else f"Re: {subject}"
    if original_message_id:
        msg["In-Reply-To"] = original_message_id
        msg["References"] = original_message_id

    msg.attach(MIMEText(body, "plain", "utf-8"))

    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode("utf-8")

    logger.info("Sending reply in thread_id=%s to=%s", thread_id, to)

    result = (
        service.users()
        .messages()
        .send(
            userId="me",
            body={"raw": raw, "threadId": thread_id},
        )
        .execute()
    )

    logger.info("Reply sent: message_id=%s", result.get("id"))

    return {"messageId": result.get("id"), "threadId": result.get("threadId")}


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------


def _mark_as_read(service, email_id: str) -> None:
    """Remove the UNREAD label from a message."""
    service.users().messages().modify(
        userId="me",
        id=email_id,
        body={"removeLabelIds": ["UNREAD"]},
    ).execute()
    logger.debug("Marked email_id=%s as read", email_id)
