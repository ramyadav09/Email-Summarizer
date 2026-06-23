from sqlalchemy.orm import Session
from app.models.email import Email, EmailSnippet
from app.core.logging import get_logger

logger = get_logger(__name__)


def get_cached_summary(db: Session, email_id: str) -> str | None:
    """Return the cached summary for an email, or None if not cached."""
    record = db.query(Email).filter(Email.email_id == email_id).first()
    if record and record.summary:
        logger.debug("Cache hit for email_id=%s", email_id)
        return record.summary
    return None


def update_summary(db: Session, email_id: str, summary: str) -> None:
    """Update the summary on an existing email record."""
    record = db.query(Email).filter(Email.email_id == email_id).first()
    if record:
        record.summary = summary
        db.commit()
        logger.info("Updated cached summary for email_id=%s", email_id)


def save_email(db: Session, email_data: dict) -> Email:
    """Persist a new email record to the database."""
    record = Email(
        email_id=email_data["email_id"],
        thread_id=email_data["thread_id"],
        from_address=email_data["from_address"],
        to_address=email_data["to_address"],
        subject=email_data["subject"],
        body_html=email_data.get("body_html"),
        body_text=email_data.get("body_text"),
        received_at=email_data.get("received_at"),
        summary=email_data.get("summary"),
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    logger.info("Saved email to database: email_id=%s", email_data["email_id"])
    return record


def save_email_snippets(db: Session, snippets: list[dict]) -> list[EmailSnippet]:
    try:
        # Standardize and extract email IDs to query existing records in batch
        email_ids = [s.get("id") or s.get("email_id") for s in snippets if s.get("id") or s.get("email_id")]
        if not email_ids:
            return []

        # Fetch existing snippets to perform update instead of duplicate insert
        existing_records = db.query(EmailSnippet).filter(EmailSnippet.email_id.in_(email_ids)).all()
        existing_map = {r.email_id: r for r in existing_records}

        processed_records = []
        for s in snippets:
            email_id = s.get("id") or s.get("email_id")
            if not email_id:
                continue

            snippet_text = s.get("snippet", "")
            subject_text = s.get("subject", "")
            
            # Map boolean is_read (from Gmail response) to DB String ("READ"/"UNREAD")
            is_read_val = s.get("is_read", False)
            if isinstance(is_read_val, bool):
                is_read_str = "READ" if is_read_val else "UNREAD"
            else:
                is_read_str = str(is_read_val)

            if email_id in existing_map:
                record = existing_map[email_id]
                record.snippet = snippet_text
                record.subject = subject_text
                record.is_read = is_read_str
            else:
                record = EmailSnippet(
                    email_id=email_id,
                    snippet=snippet_text,
                    subject=subject_text,
                    is_read=is_read_str,
                )
                db.add(record)
            
            processed_records.append(record)

        db.commit()
        logger.info("Saved/updated %d email snippets.", len(processed_records))
        return processed_records

    except Exception as e:
        db.rollback()
        logger.error("Failed to save email snippets: %s", e, exc_info=True)
        raise e

