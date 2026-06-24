"""Gmail API service — fetching, reading, and sending emails."""

import base64
import time
from datetime import datetime, timezone
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from bs4 import BeautifulSoup

from app.core.config import settings
from sqlalchemy.orm import Session
from app.core.logging import get_logger
from app.models.email import User
from fastapi import HTTPException

from app.services.email_repository import save_email_snippets, upsert_emails_full

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


def _build_service(user: User):
    """Build an authenticated Gmail API service client from user tokens."""
    if not user.google_access_token:
        raise HTTPException(status_code=403, detail="Google account not linked")

    creds = Credentials(
        token=user.google_access_token,
        refresh_token=user.google_refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=settings.CLIENT_ID,
        client_secret=settings.CLIENT_SECRET,
    )

    if creds.expired and creds.refresh_token:
        try:
            import google.auth.transport.requests

            request = google.auth.transport.requests.Request()
            creds.refresh(request)
            # We don't automatically save refreshed tokens back to DB here for simplicity,
            # but ideally we should update user.google_access_token.
        except Exception as e:
            logger.error(
                "Failed to refresh Google token for user_id=%s: %s", user.id, e
            )
            raise HTTPException(status_code=403, detail="Google account not linked")

    if not creds.valid:
        raise HTTPException(status_code=403, detail="Google account not linked")

    return build("gmail", "v1", credentials=creds)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def fetch_emails(
    user: User,
    db: Session,
    after: str | None = None,
    before: str | None = None,
    read_status: str | None = None,
) -> list[dict]:
    """Fetch emails incrementally from Gmail and store in the database."""
    service = _build_service(user)

    domains = " OR ".join(f"from:(*@{d})" for d in settings.ALLOWED_DOMAINS)
    query = f"({domains})"

    # Use user.last_email_fetched for incremental sync if not manually specified.
    # On first sync (last_email_fetched is None), use created_at as the lower
    # bound so we only pull emails that arrived after the account was created.
    last_email_fetched_ms = 0
    if not after and user.last_email_fetched:
        last_email_fetched_ms = int(user.last_email_fetched.timestamp() * 1000)
        # We query with integer seconds. Subtract 1 to avoid rounding boundaries
        epoch_sec = max(0, int(user.last_email_fetched.timestamp()) - 1)
        query += f" after:{epoch_sec}"
    elif not after and user.created_at:
        # First-ever sync: only fetch emails received after account creation
        epoch_sec = max(0, int(user.created_at.timestamp()) - 1)
        query += f" after:{epoch_sec}"
        logger.info(
            "First sync for user_id=%s — fetching emails after account created_at (%s)",
            user.id,
            user.created_at,
        )
    elif after:
        query += f" after:{after}"

    if before:
        query += f" before:{before}"
    if read_status:
        query += f" is:{read_status}"

    logger.info("Fetching emails for user_id=%s with query: %s", user.id, query)

    try:
        results = service.users().messages().list(userId="me", q=query).execute()
    except Exception as e:
        logger.error("Google API error for user_id=%s: %s", user.id, e)
        raise HTTPException(status_code=403, detail="Google account not linked")

    messages = results.get("messages", [])
    logger.info("Found %d messages to sync", len(messages))

    filtered_emails = []
    full_email_records = []
    max_internal_date_ms = last_email_fetched_ms

    for msg in messages:
        try:
            detail = (
                service.users()
                .messages()
                .get(
                    userId="me",
                    id=msg["id"],
                    format="full",
                )
                .execute()
            )
        except Exception as e:
            logger.error("Failed to fetch details for message_id=%s: %s", msg["id"], e)
            continue

        internal_date_str = detail.get("internalDate", "0")
        try:
            internal_date_ms = int(internal_date_str)
        except ValueError:
            internal_date_ms = 0

        # Strict millisecond precision check
        if internal_date_ms <= last_email_fetched_ms:
            continue

        payload = detail.get("payload", {})
        headers = {h["name"]: h["value"] for h in payload.get("headers", [])}
        label_ids = detail.get("labelIds", [])
        internal_dt = datetime.fromtimestamp(internal_date_ms / 1000.0, tz=timezone.utc)

        # Extract body content from the full payload
        body_plain = _extract_part_by_type(payload, "text/plain")
        body_html = _extract_part_by_type(payload, "text/html")
        if not body_plain and not body_html:
            body_plain = detail.get("snippet", "")

        snippet_record = {
            "id": msg["id"],
            "from": headers.get("From", ""),
            "subject": headers.get("Subject", ""),
            "snippet": detail.get("snippet", ""),
            "summary": None,
            "is_read": "UNREAD" not in label_ids,
            "internal_date": internal_dt,
        }
        filtered_emails.append(snippet_record)

        full_record = {
            "email_id": msg["id"],
            "thread_id": detail.get("threadId", ""),
            "from_address": headers.get("From", ""),
            "to_address": headers.get("To", ""),
            "subject": headers.get("Subject", ""),
            "body_text": body_plain,
            "body_html": body_html,
            "received_at": internal_dt,
        }
        full_email_records.append(full_record)

        if internal_date_ms > max_internal_date_ms:
            max_internal_date_ms = internal_date_ms

    if filtered_emails:
        save_email_snippets(db, user.id, filtered_emails)
        upsert_emails_full(db, user.id, full_email_records)

        # Update last fetched time with the highest timestamp of processed emails
        user.last_email_fetched = datetime.fromtimestamp(
            max_internal_date_ms / 1000.0, tz=timezone.utc
        )
        db.commit()
        logger.info(
            "Successfully synced %d new emails. Updated last_email_fetched to %s.",
            len(filtered_emails),
            user.last_email_fetched,
        )
    else:
        logger.info(
            "No new emails found after local millisecond precision filtering. DB operations skipped."
        )

    return filtered_emails


def fetch_email_detail(user: User, email_id: str) -> dict:
    """Fetch the full detail of a single email and mark it as read."""
    service = _build_service(user)

    logger.debug("Fetching detail for email_id=%s user_id=%s", email_id, user.id)

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
    user: User,
    thread_id: str,
    to: str,
    subject: str,
    body: str,
    original_message_id: str | None = None,
) -> dict:
    """Send a reply email within the same Gmail thread."""
    service = _build_service(user)

    msg = MIMEMultipart("alternative")
    msg["To"] = to
    msg["Subject"] = subject if subject.lower().startswith("re:") else f"Re: {subject}"
    if original_message_id:
        msg["In-Reply-To"] = original_message_id
        msg["References"] = original_message_id

    msg.attach(MIMEText(body, "plain", "utf-8"))

    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode("utf-8")

    logger.info(
        "Sending reply in thread_id=%s to=%s for user_id=%s", thread_id, to, user.id
    )

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
