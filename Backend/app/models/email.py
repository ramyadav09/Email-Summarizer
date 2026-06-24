from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import relationship
from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_email_fetched = Column(DateTime(timezone=True), nullable=True)
    google_access_token = Column(String, nullable=True)
    google_refresh_token = Column(String, nullable=True)

    emails = relationship("Email", back_populates="user")
    email_snippets = relationship("EmailSnippet", back_populates="user")

    @property
    def is_google_linked(self) -> bool:
        return bool(self.google_access_token)


class Email(Base):
    __tablename__ = "emails"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    email_id = Column(String, index=True, nullable=False)
    thread_id = Column(String, index=True)
    from_address = Column(String, nullable=False)
    to_address = Column(String, nullable=False)
    subject = Column(String, nullable=True)
    body_html = Column(Text, nullable=True)
    body_text = Column(Text, nullable=True)
    received_at = Column(DateTime, nullable=True)
    summary = Column(Text, nullable=True)

    user = relationship("User", back_populates="emails")

    __table_args__ = (
        UniqueConstraint("user_id", "email_id", name="uq_user_email"),
    )


class EmailSnippet(Base):
    __tablename__ = "email_snippets"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    email_id = Column(String, index=True, nullable=False)
    snippet = Column(String, nullable=False)
    subject = Column(String, nullable=False)
    is_read = Column(String, default="UNREAD", nullable=False)
    internal_date = Column(DateTime(timezone=True), nullable=True)

    user = relationship("User", back_populates="email_snippets")

    __table_args__ = (
        UniqueConstraint("user_id", "email_id", name="uq_user_email_snippet"),
    )
