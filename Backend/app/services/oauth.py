from google_auth_oauthlib.flow import Flow
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


def make_flow() -> Flow:
    """Create a Google OAuth 2.0 flow for Gmail authorization."""
    client_config = {
        "web": {
            "client_id": settings.CLIENT_ID,
            "client_secret": settings.CLIENT_SECRET,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
        }
    }

    logger.debug("Creating OAuth flow with redirect_uri=%s", settings.REDIRECT_URI)

    return Flow.from_client_config(
        client_config,
        scopes=settings.SCOPES,
        redirect_uri=settings.REDIRECT_URI,
    )
