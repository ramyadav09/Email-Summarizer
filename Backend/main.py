import os
import base64
import secrets
from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from starlette.middleware.sessions import SessionMiddleware
from pydantic import BaseModel
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import Flow
from langchain_mistralai import ChatMistralAI
from langchain_core.messages import HumanMessage
from dotenv import load_dotenv

load_dotenv()
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key=secrets.token_hex(32))
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def make_flow():
    client_config = {
        "web": {
            "client_id": os.getenv("CLIENT_ID"),
            "client_secret": os.getenv("CLIENT_SECRET"),
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
        }
    }
    return Flow.from_client_config(
        client_config,
        scopes=["https://www.googleapis.com/auth/gmail.readonly"],
        redirect_uri="http://localhost:8000/auth/google/callback",
    )


def gmail_service(token: str):
    creds = Credentials(token=token)
    return build("gmail", "v1", credentials=creds)


@app.get("/auth/login")
def auth_login(request: Request):
    import hashlib, base64 as b64
    code_verifier = secrets.token_urlsafe(64)
    code_challenge = b64.urlsafe_b64encode(
        hashlib.sha256(code_verifier.encode()).digest()
    ).rstrip(b"=").decode()
    request.session["code_verifier"] = code_verifier
    flow = make_flow()
    authorization_url, state = flow.authorization_url(
        access_type="offline",
        prompt="consent",
        code_challenge=code_challenge,
        code_challenge_method="S256",
    )
    request.session["oauth_state"] = state
    return RedirectResponse(authorization_url)


@app.get("/auth/google/callback")
def auth_callback(request: Request):
    import requests as req
    code = request.query_params.get("code")
    code_verifier = request.session.get("code_verifier")
    token_response = req.post(
        "https://oauth2.googleapis.com/token",
        data={
            "code": code,
            "client_id": os.getenv("CLIENT_ID"),
            "client_secret": os.getenv("CLIENT_SECRET"),
            "redirect_uri": "http://localhost:8000/auth/google/callback",
            "grant_type": "authorization_code",
            "code_verifier": code_verifier,
        },
    )
    token_data = token_response.json()
    access_token = token_data.get("access_token")
    if not access_token:
        raise HTTPException(status_code=400, detail=token_data)
    return RedirectResponse(f"http://localhost:5173/?access_token={access_token}")


@app.get("/api/emails")
def get_emails(authorization: str = Header(...)):
    token = authorization.removeprefix("Bearer ")
    try:
        service = gmail_service(token)
        results = service.users().messages().list(userId="me", maxResults=10).execute()
        messages = results.get("messages", [])
        emails = []
        for msg in messages:
            detail = service.users().messages().get(
                userId="me", id=msg["id"], format="metadata",
                metadataHeaders=["From", "Subject"]
            ).execute()
            headers = {h["name"]: h["value"] for h in detail["payload"]["headers"]}
            emails.append({
                "id": msg["id"],
                "from": headers.get("From", ""),
                "subject": headers.get("Subject", ""),
                "snippet": detail.get("snippet", ""),
                "summary": None,
            })
        return emails
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


class SummarizeRequest(BaseModel):
    id: str


@app.post("/api/summarize")
def summarize_email(req: SummarizeRequest, authorization: str = Header(...)):
    token = authorization.removeprefix("Bearer ")
    try:
        service = gmail_service(token)
        detail = service.users().messages().get(userId="me", id=req.id, format="full").execute()

        body = ""
        parts = detail.get("payload", {}).get("parts", [])
        for part in parts:
            if part.get("mimeType") == "text/plain":
                data = part["body"].get("data", "")
                body = base64.urlsafe_b64decode(data + "==").decode("utf-8", errors="ignore")
                break
        if not body:
            body = detail.get("snippet", "")

        llm = ChatMistralAI(model="mistral-large-latest", api_key=os.getenv("MISTRAL_API_KEY"))
        response = llm.invoke([HumanMessage(content=f"Summarize this email in 2 sentences:\n\n{body}")])
        return {"summary": response.content}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
