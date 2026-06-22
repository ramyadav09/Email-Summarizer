import hashlib
import base64
import secrets
import requests
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse
from app.config import CLIENT_ID, CLIENT_SECRET, REDIRECT_URI, FRONTEND_URL
from app.services.gmail import make_flow

router = APIRouter(prefix="/auth")


@router.get("/login")
def auth_login(request: Request):
    code_verifier = secrets.token_urlsafe(64)
    code_challenge = base64.urlsafe_b64encode(
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


@router.get("/google/callback")
def auth_callback(request: Request):
    code = request.query_params.get("code")
    state = request.query_params.get("state")

    if not code:
        raise HTTPException(status_code=400, detail="Missing authorization code")

    expected_state = request.session.get("oauth_state")
    if not expected_state or state != expected_state:
        raise HTTPException(status_code=400, detail="Invalid OAuth state")

    code_verifier = request.session.get("code_verifier")
    if not code_verifier:
        raise HTTPException(status_code=400, detail="Missing code verifier")

    response = requests.post(
        "https://oauth2.googleapis.com/token",
        data={
            "code": code,
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "redirect_uri": REDIRECT_URI,
            "grant_type": "authorization_code",
            "code_verifier": code_verifier,
        },
        timeout=10,
    )

    try:
        response.raise_for_status()
    except requests.HTTPError:
        raise HTTPException(
            status_code=400,
            detail=response.json(),
        )

    token_data = response.json()

    access_token = token_data.get("access_token")
    if not access_token:
        raise HTTPException(
            status_code=400,
            detail="Failed to obtain access token",
        )

    # Cleanup temporary OAuth session data
    request.session.pop("oauth_state", None)
    request.session.pop("code_verifier", None)

    return RedirectResponse(url=f"{FRONTEND_URL}/?access_token={access_token}")
