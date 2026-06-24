from sqlalchemy.orm import Session
from app.models.email import Email, EmailSnippet
from app.core.logging import get_logger

logger = get_logger(__name__)


def get_user_emails_from_db(db: Session, user_id: int, page: int = 1, limit: int = 20) -> dict:
    """Fetch emails belonging to the user directly from the database with pagination."""
    if page < 1:
        page = 1
    if limit < 1:
        limit = 20

    offset = (page - 1) * limit

    # Count total records for this user
    total = db.query(EmailSnippet).filter(EmailSnippet.user_id == user_id).count()
    
    # Query with offset and limit
    records = (
        db.query(EmailSnippet)
        .filter(EmailSnippet.user_id == user_id)
        .order_by(EmailSnippet.internal_date.desc().nullslast(), EmailSnippet.id.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    
    results = []
    for r in records:
        results.append({
            "id": r.email_id,
            "snippet": r.snippet,
            "subject": r.subject,
            "is_read": r.is_read == "READ",
        })
        
    total_pages = (total + limit - 1) // limit if limit > 0 else 0
    
    return {
        "emails": results,
        "total": total,
        "page": page,
        "limit": limit,
        "total_pages": total_pages
    }


def get_cached_summary(db: Session, user_id: int, email_id: str) -> str | None:
    """Return the cached summary for an email, or None if not cached."""
    record = db.query(Email).filter(Email.user_id == user_id, Email.email_id == email_id).first()
    if record and record.summary:
        logger.debug("Cache hit for email_id=%s, user_id=%d", email_id, user_id)
        return record.summary
    return None


def update_summary(db: Session, user_id: int, email_id: str, summary: str) -> None:
    """Update the summary on an existing email record."""
    record = db.query(Email).filter(Email.user_id == user_id, Email.email_id == email_id).first()
    if record:
        record.summary = summary
        db.commit()
        logger.info("Updated cached summary for email_id=%s, user_id=%d", email_id, user_id)


def save_email(db: Session, user_id: int, email_data: dict) -> Email:
    """Persist a new email record to the database."""
    record = Email(
        user_id=user_id,
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
    logger.info("Saved email to database: email_id=%s, user_id=%d", email_data["email_id"], user_id)
    return record


def get_email_from_db(db: Session, user_id: int, email_id: str) -> dict | None:
    """Return a full email record from the DB, or None if not cached yet."""
    record = db.query(Email).filter(
        Email.user_id == user_id, Email.email_id == email_id
    ).first()
    if not record or (not record.body_text and not record.body_html):
        return None
    return {
        "id": record.email_id,
        "thread_id": record.thread_id or "",
        "from": record.from_address or "",
        "to": record.to_address or "",
        "subject": record.subject or "",
        "body": record.body_text or "",
        "body_html": record.body_html or "",
        "snippet": "",
        "date": record.received_at.isoformat() if record.received_at else "",
        "message_id": "",
        "labels": [],
        "is_read": True,
        "summary": record.summary,
    }


def upsert_emails_full(db: Session, user_id: int, emails_data: list[dict]) -> None:
    """Batch upsert full email details (body, to/from, thread_id, etc.) into the emails table.

    Called during Gmail sync so full content is cached locally, avoiding repeated
    Gmail API calls when the user opens an individual email.
    """
    if not emails_data:
        return

    # Deduplicate incoming data by email_id to prevent IntegrityError in the same batch
    unique_data = {}
    for data in emails_data:
        eid = data.get("email_id")
        if eid:
            unique_data[eid] = data
            
    emails_data = list(unique_data.values())
    email_ids = list(unique_data.keys())

    existing = (
        db.query(Email)
        .filter(Email.user_id == user_id, Email.email_id.in_(email_ids))
        .all()
    )
    existing_map = {r.email_id: r for r in existing}

    for data in emails_data:
        eid = data.get("email_id")
        if not eid:
            continue

        if eid in existing_map:
            # Update fields but preserve an existing summary
            rec = existing_map[eid]
            rec.thread_id = data.get("thread_id", rec.thread_id)
            rec.from_address = data.get("from_address", rec.from_address)
            rec.to_address = data.get("to_address", rec.to_address)
            rec.subject = data.get("subject", rec.subject)
            if data.get("body_html"):
                rec.body_html = data["body_html"]
            if data.get("body_text"):
                rec.body_text = data["body_text"]
            if data.get("received_at"):
                rec.received_at = data["received_at"]
        else:
            rec = Email(
                user_id=user_id,
                email_id=eid,
                thread_id=data.get("thread_id", ""),
                from_address=data.get("from_address", ""),
                to_address=data.get("to_address", ""),
                subject=data.get("subject", ""),
                body_html=data.get("body_html"),
                body_text=data.get("body_text"),
                received_at=data.get("received_at"),
                summary=None,
            )
            db.add(rec)

    try:
        db.commit()
        logger.info(
            "Upserted %d full email records for user_id=%d.", len(emails_data), user_id
        )
    except Exception as e:
        db.rollback()
        logger.error("Failed to upsert full email records: %s", e, exc_info=True)
        raise


def save_email_snippets(db: Session, user_id: int, snippets: list[dict]) -> list[EmailSnippet]:
    try:
        if not snippets:
            return []
            
        # Deduplicate incoming snippets by email_id to prevent IntegrityError
        unique_snippets = {}
        for s in snippets:
            eid = s.get("id") or s.get("email_id")
            if eid:
                unique_snippets[eid] = s
                
        snippets = list(unique_snippets.values())
        email_ids = list(unique_snippets.keys())
        
        if not email_ids:
            return []

        existing_records = db.query(EmailSnippet).filter(
            EmailSnippet.user_id == user_id, 
            EmailSnippet.email_id.in_(email_ids)
        ).all()
        existing_map = {r.email_id: r for r in existing_records}

        processed_records = []
        for s in snippets:
            email_id = s.get("id") or s.get("email_id")
            if not email_id:
                continue

            snippet_text = s.get("snippet", "")
            subject_text = s.get("subject", "")
            internal_date_val = s.get("internal_date")
            
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
                if internal_date_val:
                    record.internal_date = internal_date_val
            else:
                record = EmailSnippet(
                    user_id=user_id,
                    email_id=email_id,
                    snippet=snippet_text,
                    subject=subject_text,
                    is_read=is_read_str,
                    internal_date=internal_date_val,
                )
                db.add(record)
            
            processed_records.append(record)

        db.commit()
        logger.info("Saved/updated %d email snippets for user_id=%d.", len(processed_records), user_id)
        return processed_records

    except Exception as e:
        db.rollback()
        logger.error("Failed to save email snippets: %s", e, exc_info=True)
        raise e
