import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from app.core.config import settings
from app.core.database import create_tables
from app.core.logging import setup_logging, get_logger
from app.routers import auth, emails

# Set up structured logging early in the app lifecycle
setup_logging()
logger = get_logger(__name__)

# Configure insecure transport for OAuth in development mode only
if settings.DEBUG:
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
    logger.warning("OAUTHLIB_INSECURE_TRANSPORT is set to '1'. This configuration should not be used in production.")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing database tables...")
    create_tables()
    logger.info("Application startup complete.")
    yield
    logger.info("Application shutdown initiated.")

app = FastAPI(
    title="Email Summarizer API",
    description="A production-ready API for summarizing and managing emails using AI.",
    version="1.0.0",
    lifespan=lifespan
)

# Add Session Middleware using the configured SECRET_KEY
app.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KEY)

# Add CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Root/Health check endpoints
@app.get("/health", tags=["Health"])
def health_check():
    """Health check endpoint to verify backend service status."""
    return {"status": "healthy"}

# Register Routers
app.include_router(auth.router)
app.include_router(emails.router)

