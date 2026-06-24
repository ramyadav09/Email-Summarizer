from sqlalchemy.orm import Session
from app.models.email import User
from app.core.security import hash_password, verify_password

def register_user(db: Session, name: str, email: str, password: str) -> User:
    """Register a new user."""
    existing = db.query(User).filter(User.email == email).first()
    if existing:
        raise ValueError(f"A user with email '{email}' already exists.")
    
    hashed = hash_password(password)
    user = User(name=name, email=email, password_hash=hashed)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def authenticate_user(db: Session, email: str, password: str) -> User | None:
    """Authenticate user with email and password."""
    user = db.query(User).filter(User.email == email).first()
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user

def link_google_tokens(db: Session, user_id: int, access_token: str, refresh_token: str | None = None) -> User:
    """Link Google OAuth tokens to a user."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise ValueError("User not found.")
    
    user.google_access_token = access_token
    if refresh_token:
        user.google_refresh_token = refresh_token
        
    db.commit()
    db.refresh(user)
    return user
