"""Email router — inbox, detail, summarization, reply generation, and sending."""

import email.utils

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.logging import get_logger
from app.models.email import User
from app.schemas.email import (
    SummarizeRequest,
    SummarizeResponse,
    GenerateReplyRequest,
    GenerateReplyResponse,
    SendReplyRequest,
    SendReplyResponse,
)
from app.services.gmail import fetch_emails, fetch_email_detail, send_reply
from app.services.email_repository import get_cached_summary, update_summary, save_email, get_user_emails_from_db, get_email_from_db
from app.services.generation import summarize, generate_reply

logger = get_logger(__name__)

router = APIRouter(prefix="/api", tags=["emails"])


@router.get("/emails")
def get_emails(
    page: int = 1,
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Fetch inbox emails directly from the database for the current user with pagination."""
    try:
        return get_user_emails_from_db(db, current_user.id, page=page, limit=limit)
    except Exception as exc:
        logger.error("Failed to fetch emails from DB: %s", exc, exc_info=True)
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/emails/sync")
def sync_emails(
    page: int = 1,
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    after: str = None,
    before: str = None,
    read_status: str = None,
    db: Session = Depends(get_db),
):
    """Sync emails from Google to the database, then return the updated paginated list (empty emails array if 0 new)."""
    try:
        new_emails = fetch_emails(
            current_user, db, after=after, before=before, read_status=read_status
        )
        result = get_user_emails_from_db(db, current_user.id, page=page, limit=limit)
        result["new_emails_count"] = len(new_emails)
        if len(new_emails) == 0:
            result["emails"] = []
        return result
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Failed to sync emails from Google: %s", exc, exc_info=True)
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/emails/{email_id}")
def get_email_by_id(
    email_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Fetch full detail of a single email — from DB cache first, Gmail fallback."""
    try:
        cached = get_email_from_db(db, current_user.id, email_id)
        if cached:
            logger.info("Serving email_id=%s from DB cache for user_id=%s", email_id, current_user.id)
            return cached
        # Not in DB yet — fetch from Gmail (marks as read) and return
        logger.info("Cache miss for email_id=%s — fetching from Gmail", email_id)
        return fetch_email_detail(current_user, email_id)
    except Exception as exc:
        logger.error("Failed to fetch email_id=%s: %s", email_id, exc, exc_info=True)
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/summarize", response_model=SummarizeResponse)
def summarize_email(
    req: SummarizeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Summarize an email body using AI. Returns cached summary if available."""
    # Check cache first
    cached = get_cached_summary(db, current_user.id, req.id)
    if cached:
        logger.info("Returning cached summary for email_id=%s", req.id)
        return SummarizeResponse(summary=cached)

    try:
        # Resolve email body text
        body_text = req.body
        detail = None
        if not body_text:
            detail = fetch_email_detail(current_user, req.id)
            body_text = (
                detail.get("body")
                or detail.get("body_html")
                or detail.get("snippet", "")
            )

        # Generate summary via LLM
        summary_text = summarize(body_text)

        # Persist to cache
        if get_cached_summary(db, current_user.id, req.id) is None:
            # Build full email data for a new record
            if not detail:
                try:
                    detail = fetch_email_detail(current_user, req.id)
                except Exception:
                    detail = {}

            received_dt = None
            if detail.get("date"):
                try:
                    received_dt = email.utils.parsedate_to_datetime(detail["date"])
                except Exception:
                    pass

            save_email(
                db,
                current_user.id,
                {
                    "email_id": req.id,
                    "thread_id": detail.get("thread_id", ""),
                    "from_address": detail.get("from", "Unknown"),
                    "to_address": detail.get("to", "Unknown"),
                    "subject": detail.get("subject", ""),
                    "body_html": detail.get("body_html"),
                    "body_text": detail.get("body") or body_text,
                    "received_at": received_dt,
                    "summary": summary_text,
                },
            )
        else:
            update_summary(db, current_user.id, req.id, summary_text)

        logger.info("Generated and cached summary for email_id=%s", req.id)
        return SummarizeResponse(summary=summary_text)

    except Exception as exc:
        logger.error("Failed to summarize email_id=%s: %s", req.id, exc, exc_info=True)
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/generate-response", response_model=GenerateReplyResponse)
def generate_response(
    req: GenerateReplyRequest,
    current_user: User = Depends(get_current_user),
):
    """Generate an AI-drafted reply to a given email."""
    try:
        # Use pre-fetched email data from frontend, fallback to fetching
        if req.body and req.from_addr and req.subject:
            email_data = {
                "from": req.from_addr,
                "subject": req.subject,
                "body": req.body,
            }
        else:
            detail = fetch_email_detail(current_user, req.id)
            email_data = {
                "from": detail.get("from", ""),
                "subject": detail.get("subject", ""),
                "body": (
                    detail.get("body")
                    or detail.get("body_html")
                    or detail.get("snippet", "")
                ),
            }

        reply = generate_reply(email_data)
        return GenerateReplyResponse(reply=reply)

    except Exception as exc:
        logger.error(
            "Failed to generate reply for email_id=%s: %s", req.id, exc, exc_info=True
        )
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/send-reply", response_model=SendReplyResponse)
def send_reply_endpoint(
    req: SendReplyRequest,
    current_user: User = Depends(get_current_user),
):
    """Send a reply email within the same Gmail thread."""
    try:
        result = send_reply(
            user=current_user,
            thread_id=req.thread_id,
            to=req.to,
            subject=req.subject,
            body=req.body,
            original_message_id=req.message_id or None,
        )
        return SendReplyResponse(
            messageId=result.get("messageId", ""),
            threadId=result.get("threadId", ""),
        )

    except Exception as exc:
        logger.error("Failed to send reply: %s", exc, exc_info=True)
        raise HTTPException(status_code=400, detail=str(exc))
