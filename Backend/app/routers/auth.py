"""Authentication router — Google OAuth 2.0 login flow."""

import hashlib
import base64
import secrets

import httpx
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse

from app.core.config import settings
from app.core.logging import get_logger
from app.services.oauth import make_flow

logger = get_logger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/login")
def auth_login(request: Request):
    """Initiate the Google OAuth 2.0 login flow with PKCE."""
    code_verifier = secrets.token_urlsafe(64)
    code_challenge = (
        base64.urlsafe_b64encode(hashlib.sha256(code_verifier.encode()).digest())
        .rstrip(b"=")
        .decode()
    )
    request.session["code_verifier"] = code_verifier

    flow = make_flow()
    authorization_url, state = flow.authorization_url(
        access_type="offline",
        prompt="consent",
        code_challenge=code_challenge,
        code_challenge_method="S256",
    )
    request.session["oauth_state"] = state

    logger.info("OAuth login initiated, redirecting to Google")
    return RedirectResponse(authorization_url)


@router.get("/google/callback")
def auth_callback(request: Request):
    """Handle the Google OAuth 2.0 callback and exchange code for token."""
    code = request.query_params.get("code")
    state = request.query_params.get("state")

    if not code:
        logger.warning("OAuth callback missing authorization code")
        raise HTTPException(status_code=400, detail="Missing authorization code")

    expected_state = request.session.get("oauth_state")
    if not expected_state or state != expected_state:
        logger.warning("OAuth callback state mismatch")
        raise HTTPException(status_code=400, detail="Invalid OAuth state")

    code_verifier = request.session.get("code_verifier")
    if not code_verifier:
        logger.warning("OAuth callback missing code verifier in session")
        raise HTTPException(status_code=400, detail="Missing code verifier")

    # Exchange authorization code for access token
    try:
        response = httpx.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": code,
                "client_id": settings.CLIENT_ID,
                "client_secret": settings.CLIENT_SECRET,
                "redirect_uri": settings.REDIRECT_URI,
                "grant_type": "authorization_code",
                "code_verifier": code_verifier,
            },
            timeout=10,
        )
        response.raise_for_status()
    except httpx.HTTPStatusError:
        logger.error("Token exchange failed: %s", response.text)
        raise HTTPException(status_code=400, detail=response.json())
    except httpx.RequestError as exc:
        logger.error("Token exchange network error: %s", exc)
        raise HTTPException(status_code=502, detail="Failed to connect to Google OAuth")

    token_data = response.json()
    access_token = token_data.get("access_token")

    if not access_token:
        logger.error("Token exchange response missing access_token")
        raise HTTPException(status_code=400, detail="Failed to obtain access token")

    # Cleanup temporary OAuth session data
    request.session.pop("oauth_state", None)
    request.session.pop("code_verifier", None)

    logger.info("OAuth flow completed successfully")
    return RedirectResponse(url=f"{settings.FRONTEND_URL}/?access_token={access_token}")
