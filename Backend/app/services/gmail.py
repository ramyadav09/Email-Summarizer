import base64
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import Flow
from app.config import CLIENT_ID, CLIENT_SECRET, REDIRECT_URI, SCOPES, ALLOWED_DOMAINS


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
        emails.append(
            {
                "id": msg["id"],
                "from": headers.get("From", ""),
                "subject": headers.get("Subject", ""),
                "snippet": detail.get("snippet", ""),
                "summary": None,
            }
        )
    return emails


def fetch_email_body(token: str, email_id: str) -> str:
    service = get_gmail_service(token)
    detail = (
        service.users()
        .messages()
        .get(userId="me", id=email_id, format="full")
        .execute()
    )
    payload = detail.get("payload", {})
    plain = _extract_part_by_type(payload, "text/plain")
    if plain:
        return plain
    html = _extract_part_by_type(payload, "text/html")
    if html:
        return html
    return detail.get("snippet", "")


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

    return {
        "id": email_id,
        "from": headers.get("From", ""),
        "to": headers.get("To", ""),
        "subject": headers.get("Subject", ""),
        "snippet": detail.get("snippet", ""),
        "body": body_plain,
        "body_html": body_html,
        "date": headers.get("Date", ""),
        "labels": labels,
    }
