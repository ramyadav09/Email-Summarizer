import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import Flow
from app.config import CLIENT_ID, CLIENT_SECRET, REDIRECT_URI, SCOPES, ALLOWED_DOMAINS
from bs4 import BeautifulSoup


def _decode_body(data: str) -> str:
    """Decode base64url-encoded email body data."""
    return base64.urlsafe_b64decode(data + "==").decode("utf-8", errors="ignore")


def _extract_part_by_type(payload, mime_type: str) -> str:
    """Recursively walk MIME parts to find a specific mime type."""
    if payload.get("mimeType") == mime_type and payload.get("body", {}).get("data"):
        return _decode_body(payload["body"]["data"])

    for part in payload.get("parts", []):
        result = _extract_part_by_type(part, mime_type)
        if result:
            return result
    return ""


def make_flow() -> Flow:
    client_config = {
        "web": {
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
        }
    }
    return Flow.from_client_config(
        client_config, scopes=SCOPES, redirect_uri=REDIRECT_URI
    )


def get_gmail_service(token: str):
    creds = Credentials(token=token)
    return build("gmail", "v1", credentials=creds)


def fetch_emails(
    token: str, after: str = None, before: str = None, read_status: str = None
) -> list:
    service = get_gmail_service(token)
    domains = " OR ".join(f"from:(*@{domain})" for domain in ALLOWED_DOMAINS)
    query = f"({domains})"
    if after:
        query += f" after:{after}"
    if before:
        query += f" before:{before}"
    if read_status:
        query += f" is:{read_status}"
    results = (
        service.users().messages().list(userId="me", q=query, maxResults=20).execute()
    )  # return msg's ids
    messages = results.get("messages", [])
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
        )
        headers = {h["name"]: h["value"] for h in detail["payload"]["headers"]}
        label_ids = detail.get("labelIds", [])
        emails.append(
            {
                "id": msg["id"],
                "from": headers.get("From", ""),
                "subject": headers.get("Subject", ""),
                "snippet": detail.get("snippet", ""),
                "summary": None,
                "is_read": "UNREAD" not in label_ids,
            }
        )
    return emails


def get_thread_id(token: str, email_id: str):

    service = get_gmail_service(token)
    message = service.users().messages().get(userId="me", id=email_id).execute()
    return message["threadId"]


def fetch_email_body(token: str, email_id: str) -> dict:
    service = get_gmail_service(token)

    detail = (
        service.users()
        .messages()
        .get(userId="me", id=email_id, format="full")
        .execute()
    )

    payload = detail.get("payload", {})

    headers = {h["name"]: h["value"] for h in payload.get("headers", [])}

    body = _extract_part_by_type(payload, "text/plain")
    if not body:
        html = _extract_part_by_type(payload, "text/html")
        if html:
            body = BeautifulSoup(html, "html.parser").get_text(
                separator=" ",
                strip=True,
            )

    if not body:
        body = detail.get("snippet", "")

    return {
        "subject": headers.get("Subject", ""),
        "from": headers.get("From", ""),
        "to": headers.get("To", ""),
        "date": headers.get("Date", ""),
        "body": body,
    }


def mark_as_read(token: str, email_id: str):
    """Remove the UNREAD label from a message to mark it as read."""
    service = get_gmail_service(token)
    service.users().messages().modify(
        userId="me",
        id=email_id,
        body={"removeLabelIds": ["UNREAD"]},
    ).execute()


def fetch_email_detail(token: str, email_id: str) -> dict:
    service = get_gmail_service(token)
    detail = (
        service.users()
        .messages()
        .get(userId="me", id=email_id, format="full")
        .execute()
    )
    payload = detail.get("payload", {})
    headers = {h["name"]: h["value"] for h in payload.get("headers", [])}

    # extract plain text and html bodies
    body_plain = _extract_part_by_type(payload, "text/plain")
    body_html = _extract_part_by_type(payload, "text/html")

    # fallback: if neither found, use snippet
    if not body_plain and not body_html:
        body_plain = detail.get("snippet", "")

    # extract labels
    labels = detail.get("labelIds", [])
    is_read = "UNREAD" not in labels

    # mark as read in Gmail
    if not is_read:
        try:
            mark_as_read(token, email_id)
        except Exception:
            pass  # non-critical, don't block the response

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
    original_message_id: str = None,
) -> dict:
    """Send a reply email within the same Gmail thread."""
    service = get_gmail_service(token)

    msg = MIMEMultipart("alternative")
    msg["To"] = to
    msg["Subject"] = subject if subject.lower().startswith("re:") else f"Re: {subject}"
    if original_message_id:
        msg["In-Reply-To"] = original_message_id
        msg["References"] = original_message_id

    msg.attach(MIMEText(body, "plain", "utf-8"))

    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode("utf-8")

    result = (
        service.users()
        .messages()
        .send(
            userId="me",
            body={"raw": raw, "threadId": thread_id},
        )
        .execute()
    )

    return {"messageId": result.get("id"), "threadId": result.get("threadId")}
