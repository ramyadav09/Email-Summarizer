"""Authentication router — user registration, login, and Google OAuth 2.0 flow."""

import hashlib
import base64
import secrets

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.logging import get_logger
from app.core.security import create_access_token
from app.models.email import User
from app.schemas.user import TokenResponse, UserLoginRequest, UserRegisterRequest, UserResponse
from app.services.oauth import make_flow
from app.services.user_service import (
    authenticate_user,
    link_google_tokens,
    register_user,
)

logger = get_logger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])


# ---------------------------------------------------------------------------
# Email/Password Auth
# ---------------------------------------------------------------------------


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def auth_register(req: UserRegisterRequest, db: Session = Depends(get_db)):
    """Register a new user with name, email, and password."""
    try:
        user = register_user(db, name=req.name, email=req.email, password=req.password)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))

    token = create_access_token(user.id, user.email)
    logger.info("New user registered: user_id=%d", user.id)
    return TokenResponse(
        access_token=token,
        user=UserResponse.model_validate(user),
    )


@router.post("/login", response_model=TokenResponse)
def auth_login_password(req: UserLoginRequest, db: Session = Depends(get_db)):
    """Authenticate with email and password."""
    user = authenticate_user(db, email=req.email, password=req.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    token = create_access_token(user.id, user.email)
    logger.info("User logged in: user_id=%d", user.id)
    return TokenResponse(
        access_token=token,
        user=UserResponse.model_validate(user),
    )


@router.get("/me", response_model=UserResponse)
def auth_get_me(current_user: User = Depends(get_current_user)):
    """Get the current authenticated user's profile."""
    return UserResponse.model_validate(current_user)


# ---------------------------------------------------------------------------
# Google OAuth — links Gmail to an existing authenticated user account
# ---------------------------------------------------------------------------


@router.get("/google")
def auth_google(
    request: Request,
    current_user: User = Depends(get_current_user),
):
    """Initiate the Google OAuth 2.0 flow. Redirects user directly to Google."""
    from fastapi.responses import RedirectResponse
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
    # Store the user_id so the callback knows which user to link
    request.session["oauth_user_id"] = current_user.id

    logger.info("Google OAuth initiated for user_id=%d", current_user.id)
    return RedirectResponse(url=authorization_url)


@router.get("/google/callback")
def auth_google_callback(request: Request, db: Session = Depends(get_db)):
    """Handle the Google OAuth 2.0 callback."""
    from fastapi.responses import RedirectResponse
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

    user_id: int | None = request.session.get("oauth_user_id")
    if user_id is None:
        raise HTTPException(
            status_code=400,
            detail="OAuth session missing user context. Please start the flow again.",
        )

    # Exchange authorization code for tokens
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
    refresh_token = token_data.get("refresh_token")

    if not access_token:
        logger.error("Token exchange response missing access_token")
        raise HTTPException(status_code=400, detail="Failed to obtain access token")

    # Persist Google tokens to the user record
    link_google_tokens(db, user_id=user_id, access_token=access_token, refresh_token=refresh_token)

    # Cleanup temporary OAuth session data
    request.session.pop("oauth_state", None)
    request.session.pop("code_verifier", None)
    request.session.pop("oauth_user_id", None)

    logger.info("Google OAuth completed for user_id=%d", user_id)

    # Issue a fresh JWT and redirect to frontend
    user = db.query(User).filter(User.id == user_id).first()
    jwt_token = create_access_token(user.id, user.email)
    return RedirectResponse(url=f"{settings.FRONTEND_URL}/?access_token={jwt_token}")
