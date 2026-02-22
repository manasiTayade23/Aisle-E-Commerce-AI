"""JWT auth and user registration/login for cart persistence."""

from datetime import datetime, timedelta
from typing import Optional

import jwt
from fastapi import HTTPException, Header
from passlib.context import CryptContext
from pydantic import BaseModel

from app.config import JWT_SECRET, JWT_ALGORITHM, JWT_EXPIRY_HOURS
from app.database import SessionLocal, User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class RegisterRequest(BaseModel):
    email: str
    password: str
    name: Optional[str] = None


class LoginRequest(BaseModel):
    email: str
    password: str


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_token(user_id: int, email: str) -> str:
    payload = {
        "sub": str(user_id),
        "email": email,
        "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRY_HOURS),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except Exception:
        return None


def get_current_user_id(authorization: Optional[str] = Header(None)) -> Optional[int]:
    """Return user_id from Authorization Bearer token, or None if missing/invalid."""
    if not authorization or not authorization.startswith("Bearer "):
        return None
    token = authorization.replace("Bearer ", "").strip()
    payload = decode_token(token)
    if not payload or "sub" not in payload:
        return None
    try:
        return int(payload["sub"])
    except (ValueError, TypeError):
        return None


def register_user(email: str, password: str, name: Optional[str] = None) -> dict:
    """Create user and return { user_id, email, name, access_token }."""
    db = SessionLocal()
    try:
        if db.query(User).filter(User.email == email).first():
            raise HTTPException(status_code=400, detail="Email already registered")
        user = User(
            email=email,
            name=name or email.split("@")[0],
            password_hash=hash_password(password),
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        token = create_token(user.id, user.email)
        return {
            "user_id": user.id,
            "email": user.email,
            "name": user.name,
            "access_token": token,
        }
    finally:
        db.close()


def login_user(email: str, password: str) -> dict:
    """Verify credentials and return { user_id, email, name, access_token }."""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        if not user or not user.password_hash:
            raise HTTPException(status_code=401, detail="Invalid email or password")
        if not verify_password(password, user.password_hash):
            raise HTTPException(status_code=401, detail="Invalid email or password")
        token = create_token(user.id, user.email)
        return {
            "user_id": user.id,
            "email": user.email,
            "name": user.name,
            "access_token": token,
        }
    finally:
        db.close()
