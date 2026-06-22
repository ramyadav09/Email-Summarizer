import base64
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import Flow
from app.config import CLIENT_ID, CLIENT_SECRET, REDIRECT_URI, SCOPES, ALLOWED_DOMAINS


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


def fetch_emails(token: str, after: str = None, before: str = None) -> list:
    service = get_gmail_service(token)
    domains = " OR ".join(f"from:(*@{domain})" for domain in ALLOWED_DOMAINS)
    query = f"({domains})"
    if after:
        query += f" after:{after}"
    if before:
        query += f" before:{before}"
    results = (
        service.users()
        .messages()
        .list(userId="me", q=query, maxResults=10)
        .execute()
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
    for part in detail.get("payload", {}).get("parts", []):
        if part.get("mimeType") == "text/plain":
            data = part["body"].get("data", "")
            return base64.urlsafe_b64decode(data + "==").decode(
                "utf-8", errors="ignore"
            )
    return detail.get("snippet", "")
