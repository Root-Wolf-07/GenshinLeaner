"""FastAPI dependencies, security helpers, and authentication context.
Supports JWT authentication with standard library fallback for maximum resilience.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
from datetime import datetime, timezone, timedelta
from typing import Generator, Optional, Tuple

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from backend.config import settings
from backend.db.session import get_db
from backend.models.user import User

# HTTP Bearer security scheme
security_scheme = HTTPBearer(auto_error=False)

try:
    import bcrypt
    HAS_BCRYPT = True
except ImportError:
    HAS_BCRYPT = False


# Password Hashing Utilities
def hash_password(password: str) -> str:
    """Hash a password securely using bcrypt with PBKDF2 fallback."""
    if HAS_BCRYPT:
        pw_bytes = password.encode("utf-8")[:72]
        return bcrypt.hashpw(pw_bytes, bcrypt.gensalt()).decode("utf-8")
    # Standard library fallback: PBKDF2 with HMAC-SHA256
    salt = hashlib.sha256(str(time.time()).encode()).hexdigest()[:16]
    derived = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100_000)
    return f"pbkdf2_sha256${salt}${derived.hex()}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against stored hash."""
    if not plain_password or not hashed_password:
        return False
    if HAS_BCRYPT and (hashed_password.startswith("$2a$") or hashed_password.startswith("$2b$") or hashed_password.startswith("$2y$")):
        try:
            pw_bytes = plain_password.encode("utf-8")[:72]
            return bcrypt.checkpw(pw_bytes, hashed_password.encode("utf-8"))
        except Exception:
            return False
    if hashed_password.startswith("pbkdf2_sha256$"):
        parts = hashed_password.split("$")
        if len(parts) == 3:
            _, salt, hash_hex = parts
            derived = hashlib.pbkdf2_hmac("sha256", plain_password.encode("utf-8"), salt.encode("utf-8"), 100_000)
            return hmac.compare_digest(derived.hex(), hash_hex)
    return False


# JWT Token Utilities
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a signed JWT access token."""
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": int(expire.timestamp()), "iat": int(now.timestamp())})

    # Standard compact JWT implementation
    header = {"alg": "HS256", "typ": "JWT"}
    header_b64 = base64.urlsafe_b64encode(json.dumps(header).encode()).decode().rstrip("=")
    payload_b64 = base64.urlsafe_b64encode(json.dumps(to_encode).encode()).decode().rstrip("=")
    signature_data = f"{header_b64}.{payload_b64}".encode()
    signature = hmac.new(settings.SECRET_KEY.encode(), signature_data, hashlib.sha256).digest()
    sig_b64 = base64.urlsafe_b64encode(signature).decode().rstrip("=")
    return f"{header_b64}.{payload_b64}.{sig_b64}"


def decode_access_token(token: str) -> Optional[dict]:
    """Decode and verify a signed JWT access token."""
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None
        header_b64, payload_b64, sig_b64 = parts

        # Verify signature
        signature_data = f"{header_b64}.{payload_b64}".encode()
        expected_sig = hmac.new(settings.SECRET_KEY.encode(), signature_data, hashlib.sha256).digest()
        # Add padding back if necessary
        pad = len(sig_b64) % 4
        if pad:
            sig_b64 += "=" * (4 - pad)
        actual_sig = base64.urlsafe_b64decode(sig_b64.encode())
        if not hmac.compare_digest(expected_sig, actual_sig):
            return None

        # Decode payload
        pad_payload = len(payload_b64) % 4
        if pad_payload:
            payload_b64 += "=" * (4 - pad_payload)
        payload = json.loads(base64.urlsafe_b64decode(payload_b64.encode()).decode())

        # Check expiration
        exp = payload.get("exp")
        if exp and exp < time.time():
            return None

        return payload
    except Exception:
        return None


# Demo User Helper (ensures seamless developer and frontend testing without auth blocks)
DEMO_USER_ID = "00000000-0000-0000-0000-000000000001"
DEMO_USER_EMAIL = "student@studyaid.ai"
DEMO_USERNAME = "demo_student"


def get_or_create_demo_user(db: Session) -> User:
    """Retrieve or create the demo user for development and testing."""
    user = db.query(User).filter(User.id == DEMO_USER_ID).first()
    if not user:
        user = User(
            id=DEMO_USER_ID,
            student_id="STU-DEMO0001",
            email=DEMO_USER_EMAIL,
            normalized_email=DEMO_USER_EMAIL,
            username=DEMO_USERNAME,
            hashed_password=hash_password("DemoStudentPass123!"),
            full_name="Alex Rivera",
            student_level="undergraduate",
            is_verified=True,
            session_version=1,
            preferences={
                "learning_goals": ["Master Data Structures & Algorithms", "Ace Midterm Exams"],
                "preferred_depth": "detailed",
                "study_language": "English",
                "theme": "dark",
                "katex_enabled": True,
            },
            is_active=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    else:
        # Ensure demo user has all schema fields populated
        updated = False
        if not getattr(user, "student_id", None):
            user.student_id = "STU-DEMO0001"
            updated = True
        if not getattr(user, "normalized_email", None):
            user.normalized_email = DEMO_USER_EMAIL
            updated = True
        if not getattr(user, "is_verified", False):
            user.is_verified = True
            updated = True
        if not getattr(user, "session_version", None):
            user.session_version = 1
            updated = True
        if updated:
            db.commit()
            db.refresh(user)
    return user


def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Dependency that authenticates the student via JWT bearer token or HttpOnly cookie.
    Enforces expiration, account activity, verification status, and session versioning.
    """
    token = None
    if credentials and credentials.credentials:
        token = credentials.credentials
    elif request and hasattr(request, "cookies") and "access_token" in request.cookies:
        token = request.cookies.get("access_token")

    if token:
        payload = decode_access_token(token)
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        user_id = payload.get("sub")
        if user_id:
            user = db.query(User).filter(User.id == user_id, User.is_active == True).first()  # noqa: E712
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Student account not found or deactivated",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            if not user.is_verified:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Student account requires verification before accessing protected learning data.",
                )
            token_session_ver = payload.get("session_version", 1)
            if getattr(user, "session_version", 1) != token_session_ver:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Session has been revoked. Please sign in again.",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            return user

    # Development auto-provision fallback ONLY if explicitly set
    if (settings.DEBUG or settings.APP_ENV == "development") and getattr(settings, "DEV_AUTO_DEMO_USER", False):
        return get_or_create_demo_user(db)

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required",
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_optional_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
    db: Session = Depends(get_db),
) -> Optional[User]:
    """Dependency for public routes that can optionally tailor responses to authenticated users."""
    try:
        return get_current_user(request, credentials, db)
    except HTTPException:
        return None
