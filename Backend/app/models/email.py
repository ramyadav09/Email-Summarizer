from sqlalchemy import Column, Integer, String, DateTime, Text
from app.core.database import Base


class Email(Base):
    __tablename__ = "emails"

    id = Column(Integer, primary_key=True, index=True)
    email_id = Column(String, unique=True, index=True, nullable=False)
    thread_id = Column(String, index=True)
    from_address = Column(String, nullable=False)
    to_address = Column(String, nullable=False)
    subject = Column(String, nullable=True)
    body_html = Column(Text, nullable=True)
    body_text = Column(Text, nullable=True)
    received_at = Column(DateTime, nullable=True)
    summary = Column(Text, nullable=True)


class EmailSnippet(Base):
    __tablename__ = "email_snippets"

    id = Column(Integer, primary_key=True, index=True)
    email_id = Column(String, unique=True, index=True, nullable=False)
    snippet = Column(String, nullable=False)
    subject = Column(String, nullable=False)
    is_read = Column(String, default="UNREAD", nullable=False)
