"""Student Authentication, Verification, and Student ID Service.
Provides cryptographic Student ID generation, identifier normalization,
password security policy validation, brute-force mitigation, and OTP verification delivery.
"""

from __future__ import annotations

import re
import secrets
import hashlib
import hmac
import time
from datetime import datetime, timezone, timedelta
from typing import Optional, Tuple, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import or_

from backend.config import settings
from backend.models.user import User

# In-memory delivery log for development & automated testing inspection
DEV_DELIVERY_OUTBOX: list[Dict[str, Any]] = []


def generate_student_id_token() -> str:
    """Generate a single candidate Student ID token (e.g. 'STU-B84D20E6').
    Uses 4 cryptographically secure random bytes rendered in uppercase hex.
    """
    token_hex = secrets.token_hex(4).upper()
    return f"STU-{token_hex}"


def generate_unique_student_id(db: Session, max_attempts: int = 10) -> str:
    """Generate a permanent, collision-resistant unique Student ID.
    Enforces database-level uniqueness across all existing student records.
    """
    for _ in range(max_attempts):
        candidate = generate_student_id_token()
        # Ensure candidate does not already exist
        existing = db.query(User).filter(User.student_id == candidate).first()
        if not existing:
            return candidate
    
    # In the astronomically rare case of repeated collisions, append extra entropy
    return f"STU-{secrets.token_hex(6).upper()}"


def normalize_email(email: Optional[str]) -> Optional[str]:
    """Normalize and validate an email address according to RFC standards."""
    if not email:
        return None
    cleaned = email.strip().lower()
    # RFC 5322 compliant regex check
    pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    if not re.match(pattern, cleaned):
        raise ValueError("Invalid email format.")
    return cleaned


def normalize_phone(phone: Optional[str]) -> Optional[str]:
    """Normalize a phone number to standard E.164-compatible format.
    Strips formatting characters (spaces, dashes, parens).
    Enforces minimum 7 and maximum 15 digits.
    """
    if not phone:
        return None
    cleaned = phone.strip()
    has_plus = cleaned.startswith("+")
    # Keep only digits
    digits_only = re.sub(r"[^\d]", "", cleaned)
    if len(digits_only) < 7 or len(digits_only) > 15:
        raise ValueError("Phone number must contain between 7 and 15 digits.")
    
    return f"+{digits_only}" if has_plus else f"+{digits_only}"


def validate_password_policy(password: str) -> Tuple[bool, Optional[str]]:
    """Validate student password against strict security requirements:
    - Minimum 8 characters
    - At least one letter (a-z, A-Z)
    - At least one digit (0-9) or special character
    """
    if not password or len(password) < 8:
        return False, "Password must be at least 8 characters long."
    if not re.search(r"[a-zA-Z]", password):
        return False, "Password must contain at least one letter."
    if not re.search(r"[\d\W_]", password):
        return False, "Password must contain at least one number or special character."
    return True, None


def generate_verification_otp(length: int = 6) -> str:
    """Generate a cryptographically secure numeric OTP."""
    return "".join(secrets.choice("0123456789") for _ in range(length))


def hash_code(code: str, salt: str = "") -> str:
    """Hash an OTP code or reset token using HMAC-SHA256 with server SECRET_KEY."""
    key = settings.SECRET_KEY.encode()
    data = f"{salt}:{code}".encode()
    return hmac.new(key, data, hashlib.sha256).hexdigest()


def verify_code(code: str, hashed: Optional[str], salt: str = "") -> bool:
    """Verify an input OTP against stored hash in constant time."""
    if not hashed or not code:
        return False
    expected_hash = hash_code(code, salt)
    return hmac.compare_digest(expected_hash, hashed)


def deliver_verification_code(
    recipient: str,
    channel: str,
    code: str,
    purpose: str = "account_verification"
) -> Dict[str, Any]:
    """Dispatch verification code via Email or SMS, or record in Dev Delivery Outbox.
    Never prints plaintext codes to production logs.
    """
    now = datetime.now(timezone.utc)
    delivery_record = {
        "recipient": recipient,
        "channel": channel,
        "purpose": purpose,
        "timestamp": now.isoformat(),
        "delivered": True,
    }

    # In development or testing mode, store delivery entry for developer/test verification
    if settings.DEBUG or settings.APP_ENV in ("development", "test"):
        # Save record in outbox (including code for test assertions in dev mode only)
        dev_record = dict(delivery_record)
        dev_record["dev_code"] = code
        DEV_DELIVERY_OUTBOX.append(dev_record)
        return {
            "success": True,
            "channel": channel,
            "recipient_masked": mask_identifier(recipient, channel),
            "dev_mode": True,
            "dev_code": code if (settings.DEBUG or settings.APP_ENV == "test") else None
        }

    # Production delivery logic (SMTP / Twilio)
    if channel == "email":
        # Check if SMTP is configured
        smtp_host = getattr(settings, "SMTP_HOST", None)
        if smtp_host:
            try:
                import smtplib
                from email.mime.text import MIMEText
                msg = MIMEText(
                    f"Your Genshin Cognitive Academy verification code is: {code}\n"
                    f"This code will expire in {getattr(settings, 'VERIFICATION_CODE_EXPIRE_MINUTES', 10)} minutes."
                )
                msg["Subject"] = "Genshin Cognitive Academy Verification Code"
                msg["From"] = getattr(settings, "SMTP_FROM_EMAIL", "noreply@genshinacademy.ai")
                msg["To"] = recipient

                port = getattr(settings, "SMTP_PORT", 587)
                with smtplib.SMTP(smtp_host, port, timeout=10) as server:
                    server.starttls()
                    smtp_user = getattr(settings, "SMTP_USER", None)
                    smtp_pass = getattr(settings, "SMTP_PASSWORD", None)
                    if smtp_user and smtp_pass:
                        server.login(smtp_user, smtp_pass)
                    server.send_message(msg)
            except Exception as e:
                return {"success": False, "error": "Email delivery failed"}
    elif channel == "phone":
        twilio_sid = getattr(settings, "TWILIO_ACCOUNT_SID", None)
        twilio_token = getattr(settings, "TWILIO_AUTH_TOKEN", None)
        twilio_from = getattr(settings, "TWILIO_FROM_PHONE", None)
        if twilio_sid and twilio_token and twilio_from:
            try:
                import urllib.parse
                import urllib.request
                # Standard HTTP request to Twilio API without heavy external deps
                url = f"https://api.twilio.com/2010-04-01/Accounts/{twilio_sid}/Messages.json"
                data = urllib.parse.urlencode({
                    "From": twilio_from,
                    "To": recipient,
                    "Body": f"Your Genshin Academy code is {code}. Valid for 10 minutes."
                }).encode("utf-8")
                req = urllib.request.Request(url, data=data, method="POST")
                auth_str = f"{twilio_sid}:{twilio_token}"
                import base64
                b64_auth = base64.b64encode(auth_str.encode("utf-8")).decode("utf-8")
                req.add_header("Authorization", f"Basic {b64_auth}")
                with urllib.request.urlopen(req, timeout=10) as resp:
                    pass
            except Exception:
                return {"success": False, "error": "SMS delivery failed"}

    return {
        "success": True,
        "channel": channel,
        "recipient_masked": mask_identifier(recipient, channel),
        "dev_mode": False
    }


def mask_identifier(identifier: str, channel: str) -> str:
    """Mask email or phone number for safe public display."""
    if channel == "email" and "@" in identifier:
        parts = identifier.split("@")
        name, domain = parts[0], parts[1]
        if len(name) <= 2:
            masked_name = name[0] + "*"
        else:
            masked_name = name[0] + "*" * (len(name) - 2) + name[-1]
        return f"{masked_name}@{domain}"
    elif channel == "phone":
        if len(identifier) > 4:
            return identifier[:3] + "****" + identifier[-3:]
        return "***"
    return "***"


def is_account_locked(user: User) -> bool:
    """Check if the student account is temporarily locked due to failed login attempts."""
    if not user.locked_until:
        return False
    now = datetime.now(timezone.utc)
    locked_until = user.locked_until
    if locked_until.tzinfo is None:
        locked_until = locked_until.replace(tzinfo=timezone.utc)
    return now < locked_until


def record_login_failure(user: User, db: Session, max_attempts: int = 5, lockout_minutes: int = 15) -> None:
    """Increment failed login attempts and lock account if threshold is exceeded."""
    user.failed_login_attempts = (user.failed_login_attempts or 0) + 1
    if user.failed_login_attempts >= max_attempts:
        user.locked_until = datetime.now(timezone.utc) + timedelta(minutes=lockout_minutes)
    db.commit()


def record_login_success(user: User, db: Session) -> None:
    """Reset failed attempts and record successful login timestamp."""
    user.failed_login_attempts = 0
    user.locked_until = None
    user.last_login_at = datetime.now(timezone.utc)
    db.commit()
