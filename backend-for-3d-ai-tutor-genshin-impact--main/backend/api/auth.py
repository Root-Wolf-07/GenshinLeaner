"""Student Authentication, Verification, and Profile API Endpoints.
Provides complete implementation for student registration, email/phone OTP verification,
login with brute-force lockout, password recovery, secure session cookies, and student profile management.
"""

from __future__ import annotations

import re
import uuid
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session
from sqlalchemy import or_

from backend.config import settings
from backend.db.session import get_db
from backend.dependencies import (
    get_current_user,
    hash_password,
    verify_password,
    create_access_token,
)
from backend.models.user import User
from backend.schemas.auth import (
    StudentRegister,
    StudentLogin,
    VerifyCodeRequest,
    ResendCodeRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    StudentResponse,
    AuthSessionToken,
    ProfileUpdate,
)
from backend.services.student_auth_service import (
    generate_unique_student_id,
    normalize_email,
    normalize_phone,
    validate_password_policy,
    generate_verification_otp,
    hash_code,
    verify_code,
    deliver_verification_code,
    mask_identifier,
    is_account_locked,
    record_login_failure,
    record_login_success,
)

router = APIRouter(tags=["Authentication & Student Account"])


@router.post("/auth/register", status_code=status.HTTP_201_CREATED)
def register(
    reg_in: StudentRegister,
    response: Response,
    db: Session = Depends(get_db),
):
    """Register a new student account with either email or phone number.
    Validates password security policy, generates a permanent Student ID,
    dispatches an OTP verification code, and creates an unverified account.
    """
    # 1. Terms acceptance verification
    if not reg_in.terms_accepted:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You must accept the Terms of Service and Privacy Policy to register.",
        )

    # 2. Password matching check
    if reg_in.password != reg_in.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password and confirmation password do not match.",
        )

    # 3. Password security policy check
    is_valid_pw, pw_err = validate_password_policy(reg_in.password)
    if not is_valid_pw:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=pw_err or "Password does not meet security requirements.",
        )

    # 4. Normalize and validate login identifier
    identifier = (reg_in.identifier or reg_in.email or "").strip()
    channel = reg_in.channel or ("email" if "@" in identifier else "phone")

    norm_email: Optional[str] = None
    norm_phone: Optional[str] = None

    if channel == "email" or "@" in identifier:
        channel = "email"
        try:
            norm_email = normalize_email(identifier)
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    else:
        channel = "phone"
        try:
            norm_phone = normalize_phone(identifier)
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    # 5. Check uniqueness of identifier
    if norm_email:
        existing = db.query(User).filter(
            or_(User.email == norm_email, User.normalized_email == norm_email)
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An account with this email address is already registered.",
            )
    if norm_phone:
        existing = db.query(User).filter(
            or_(User.phone == norm_phone, User.normalized_phone == norm_phone)
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An account with this phone number is already registered.",
            )

    # 6. Username generation / uniqueness check
    clean_identifier = norm_email or norm_phone or ""
    base_username = (reg_in.username or clean_identifier.split("@")[0].replace("+", "")).lower()
    candidate_username = re.sub(r"[^a-zA-Z0-9_]", "_", base_username)[:30]
    if not candidate_username or len(candidate_username) < 3:
        candidate_username = f"student_{uuid.uuid4().hex[:6]}"

    # Collision resolution for username
    suffix = 1
    final_username = candidate_username
    while db.query(User).filter(User.username == final_username).first():
        final_username = f"{candidate_username[:25]}_{suffix}"
        suffix += 1

    # 7. Generate permanent unique Student ID on backend
    student_id = generate_unique_student_id(db)

    # 8. Generate verification OTP
    otp_code = generate_verification_otp(6)
    salt = uuid.uuid4().hex
    otp_hash = hash_code(otp_code, salt)
    otp_expiry = datetime.now(timezone.utc) + timedelta(minutes=settings.VERIFICATION_CODE_EXPIRE_MINUTES)

    # 9. Create user record
    new_user = User(
        id=str(uuid.uuid4()),
        student_id=student_id,
        email=norm_email,
        phone=norm_phone,
        normalized_email=norm_email,
        normalized_phone=norm_phone,
        username=final_username,
        hashed_password=hash_password(reg_in.password),
        full_name=reg_in.full_name.strip(),
        student_level=reg_in.student_level or "undergraduate",
        is_verified=False,
        verification_channel=channel,
        verification_code_hash=f"{salt}:{otp_hash}",
        verification_code_expires_at=otp_expiry,
        verification_attempts=0,
        last_verification_sent_at=datetime.now(timezone.utc),
        session_version=1,
        preferences={
            "learning_goals": [],
            "preferred_depth": "detailed",
            "study_language": "English",
            "theme": "dark",
            "katex_enabled": True,
            "neutral_mode": False,
        },
        is_active=True,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # 10. Deliver verification OTP via designated channel
    target_contact = norm_email if channel == "email" else norm_phone
    delivery_res = deliver_verification_code(
        recipient=target_contact or "",
        channel=channel,
        code=otp_code,
        purpose="account_verification"
    )

    return {
        "message": f"Student account created successfully. A verification code has been sent via {channel}.",
        "student_id": new_user.student_id,
        "identifier": target_contact,
        "channel": channel,
        "requires_verification": True,
        "dev_code": delivery_res.get("dev_code") if delivery_res.get("dev_mode") else None,
    }


@router.post("/auth/verify", response_model=AuthSessionToken)
def verify_account(
    verify_in: VerifyCodeRequest,
    response: Response,
    db: Session = Depends(get_db),
):
    """Verify registration OTP code, activate account (is_verified=True), and issue session."""
    raw_id = verify_in.identifier.strip()
    user = db.query(User).filter(
        or_(
            User.email == raw_id.lower(),
            User.normalized_email == raw_id.lower(),
            User.phone == raw_id,
            User.normalized_phone == raw_id,
            User.username == raw_id,
            User.student_id == raw_id.upper(),
        )
    ).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student account not found.",
        )

    # Check if already verified
    if user.is_verified:
        # Create session directly
        record_login_success(user, db)
        token_str = create_access_token({
            "sub": user.id,
            "student_id": user.student_id,
            "session_version": user.session_version,
            "email": user.email,
        })
        _set_session_cookie(response, token_str)
        return AuthSessionToken(
            access_token=token_str,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=StudentResponse.model_validate(user),
        )

    # Check verification attempts limit
    if (user.verification_attempts or 0) >= settings.VERIFICATION_MAX_ATTEMPTS:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Maximum verification attempts exceeded. Please request a new verification code.",
        )

    # Check code expiration
    now = datetime.now(timezone.utc)
    exp = user.verification_code_expires_at
    if exp:
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=timezone.utc)
        if now > exp:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Verification code has expired. Please request a new code.",
            )

    # Check stored code hash
    stored_val = user.verification_code_hash
    if not stored_val or ":" not in stored_val:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active verification code found. Please request a new code.",
        )

    salt, expected_hash = stored_val.split(":", 1)
    input_code = verify_in.code.strip()

    # Support dev test OTP if in testing / dev mode
    is_match = False
    if settings.DEBUG and settings.DEV_TEST_OTP and input_code == settings.DEV_TEST_OTP:
        is_match = True
    else:
        is_match = verify_code(input_code, expected_hash, salt)

    if not is_match:
        user.verification_attempts = (user.verification_attempts or 0) + 1
        db.commit()
        remaining = settings.VERIFICATION_MAX_ATTEMPTS - user.verification_attempts
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid verification code. {remaining} attempt(s) remaining.",
        )

    # Successfully verified!
    user.is_verified = True
    user.verification_code_hash = None
    user.verification_code_expires_at = None
    user.verification_attempts = 0
    record_login_success(user, db)

    token_str = create_access_token({
        "sub": user.id,
        "student_id": user.student_id,
        "session_version": user.session_version,
        "email": user.email,
    })
    _set_session_cookie(response, token_str)

    return AuthSessionToken(
        access_token=token_str,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=StudentResponse.model_validate(user),
    )


@router.post("/auth/resend-code")
def resend_verification_code(
    req: ResendCodeRequest,
    db: Session = Depends(get_db),
):
    """Resend a new verification OTP code with rate-limit cooldown check."""
    raw_id = req.identifier.strip()
    user = db.query(User).filter(
        or_(
            User.email == raw_id.lower(),
            User.normalized_email == raw_id.lower(),
            User.phone == raw_id,
            User.normalized_phone == raw_id,
            User.student_id == raw_id.upper(),
        )
    ).first()

    if not user:
        # Return generic success to avoid account enumeration
        return {"message": "If an account exists, a new verification code has been sent."}

    if user.is_verified:
        return {"message": "Account is already verified. You can log in directly."}

    # Cooldown check
    now = datetime.now(timezone.utc)
    last_sent = user.last_verification_sent_at
    if last_sent:
        if last_sent.tzinfo is None:
            last_sent = last_sent.replace(tzinfo=timezone.utc)
        elapsed = (now - last_sent).total_seconds()
        if elapsed < settings.VERIFICATION_RESEND_COOLDOWN_SECONDS:
            remaining_secs = int(settings.VERIFICATION_RESEND_COOLDOWN_SECONDS - elapsed)
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Please wait {remaining_secs} seconds before requesting another code.",
            )

    # Generate new OTP
    otp_code = generate_verification_otp(6)
    salt = uuid.uuid4().hex
    otp_hash = hash_code(otp_code, salt)
    user.verification_code_hash = f"{salt}:{otp_hash}"
    user.verification_code_expires_at = now + timedelta(minutes=settings.VERIFICATION_CODE_EXPIRE_MINUTES)
    user.verification_attempts = 0
    user.last_verification_sent_at = now
    db.commit()

    channel = user.verification_channel or "email"
    contact = user.normalized_email if channel == "email" else user.normalized_phone
    delivery_res = deliver_verification_code(
        recipient=contact or "",
        channel=channel,
        code=otp_code,
        purpose="account_verification"
    )

    return {
        "message": f"A new verification code has been dispatched via {channel}.",
        "channel": channel,
        "dev_code": delivery_res.get("dev_code") if delivery_res.get("dev_mode") else None,
    }


@router.post("/auth/login", response_model=AuthSessionToken)
def login(
    login_in: StudentLogin,
    response: Response,
    db: Session = Depends(get_db),
):
    """Authenticate with Email or Phone Number and Password.
    Enforces brute-force lockout, verification policy, and sets secure HttpOnly cookie.
    """
    raw_id = (login_in.identifier or login_in.username_or_email or "").strip()
    if not raw_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Login identifier cannot be empty.",
        )

    # Search user by normalized email, phone, username, or Student ID
    user = db.query(User).filter(
        or_(
            User.email == raw_id.lower(),
            User.normalized_email == raw_id.lower(),
            User.phone == raw_id,
            User.normalized_phone == raw_id,
            User.username == raw_id,
            User.student_id == raw_id.upper(),
        )
    ).first()

    # Check account brute-force lock
    if user and is_account_locked(user):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Account temporarily locked due to repeated failed login attempts. Please try again in 15 minutes.",
        )

    # Verify password with generic error to avoid account harvesting
    if not user or not verify_password(login_in.password, user.hashed_password):
        if user:
            record_login_failure(user, db, max_attempts=settings.LOGIN_MAX_FAILED_ATTEMPTS, lockout_minutes=settings.LOGIN_LOCKOUT_MINUTES)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid login identifier or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check if account is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Student account is deactivated. Please contact academic support.",
        )

    # Check if verified
    if not user.is_verified:
        target_id = user.normalized_email or user.normalized_phone or user.email or user.phone
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "UNVERIFIED_ACCOUNT",
                "message": "Student account is not yet verified. Please enter the verification code sent to your contact.",
                "identifier": target_id,
                "channel": user.verification_channel or "email",
                "student_id": user.student_id,
            },
        )

    # Successful login
    record_login_success(user, db)

    # Compute expiration based on remember_me
    delta = None
    if login_in.remember_me:
        delta = timedelta(days=settings.AUTH_REMEMBER_ME_DAYS)

    token_str = create_access_token({
        "sub": user.id,
        "student_id": user.student_id,
        "session_version": getattr(user, "session_version", 1),
        "email": user.email,
    }, expires_delta=delta)

    # Set secure HttpOnly cookie
    max_age_secs = int(delta.total_seconds()) if delta else (settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60)
    _set_session_cookie(response, token_str, max_age=max_age_secs)

    return AuthSessionToken(
        access_token=token_str,
        expires_in=max_age_secs,
        user=StudentResponse.model_validate(user),
    )


@router.post("/auth/forgot-password")
def forgot_password(
    req: ForgotPasswordRequest,
    db: Session = Depends(get_db),
):
    """Request a password reset code. Returns a generic message to prevent account enumeration."""
    raw_id = req.identifier.strip()
    user = db.query(User).filter(
        or_(
            User.email == raw_id.lower(),
            User.normalized_email == raw_id.lower(),
            User.phone == raw_id,
            User.normalized_phone == raw_id,
            User.student_id == raw_id.upper(),
        )
    ).first()

    dev_code = None
    if user:
        reset_otp = generate_verification_otp(6)
        salt = uuid.uuid4().hex
        reset_hash = hash_code(reset_otp, salt)
        user.reset_token_hash = f"{salt}:{reset_hash}"
        user.reset_token_expires_at = datetime.now(timezone.utc) + timedelta(minutes=15)
        db.commit()

        channel = user.verification_channel or ("email" if user.email else "phone")
        contact = user.normalized_email or user.normalized_phone or user.email or user.phone
        res = deliver_verification_code(
            recipient=contact or "",
            channel=channel,
            code=reset_otp,
            purpose="password_reset"
        )
        if res.get("dev_mode"):
            dev_code = res.get("dev_code")

    return {
        "message": "If an account is associated with this identifier, a password reset code has been dispatched.",
        "dev_code": dev_code if settings.DEBUG else None
    }


@router.post("/auth/reset-password")
def reset_password(
    req: ResetPasswordRequest,
    db: Session = Depends(get_db),
):
    """Reset account password using single-use reset OTP.
    Invalidates all existing student sessions by bumping session_version.
    """
    if req.new_password != req.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password and confirmation do not match.",
        )

    is_valid_pw, pw_err = validate_password_policy(req.new_password)
    if not is_valid_pw:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=pw_err or "Password does not meet security requirements.",
        )

    raw_id = req.identifier.strip()
    user = db.query(User).filter(
        or_(
            User.email == raw_id.lower(),
            User.normalized_email == raw_id.lower(),
            User.phone == raw_id,
            User.normalized_phone == raw_id,
            User.student_id == raw_id.upper(),
        )
    ).first()

    if not user or not user.reset_token_hash:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired password reset code.",
        )

    # Check expiry
    now = datetime.now(timezone.utc)
    exp = user.reset_token_expires_at
    if exp:
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=timezone.utc)
        if now > exp:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password reset code has expired. Please request a new code.",
            )

    salt, expected_hash = user.reset_token_hash.split(":", 1)
    input_code = req.code.strip()

    is_match = False
    if settings.DEBUG and settings.DEV_TEST_OTP and input_code == settings.DEV_TEST_OTP:
        is_match = True
    else:
        is_match = verify_code(input_code, expected_hash, salt)

    if not is_match:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid password reset code.",
        )

    # Update password and invalidate all existing sessions
    user.hashed_password = hash_password(req.new_password)
    user.reset_token_hash = None
    user.reset_token_expires_at = None
    user.password_changed_at = now
    user.session_version = (user.session_version or 1) + 1
    user.failed_login_attempts = 0
    user.locked_until = None
    db.commit()

    return {"message": "Password updated successfully. All prior sessions have been invalidated. You can now sign in."}


@router.post("/auth/logout")
def logout(response: Response, current_user: User = Depends(get_current_user)):
    """Log out student and clear HttpOnly session cookie."""
    response.delete_cookie(
        key="access_token",
        path="/",
        httponly=True,
        samesite="lax",
    )
    return {"message": "Logged out successfully."}


@router.get("/auth/me", response_model=StudentResponse)
def get_me(current_user: User = Depends(get_current_user)):
    """Get authenticated student's identity including unique Student ID."""
    return current_user


@router.get("/profile", response_model=StudentResponse)
def get_profile(current_user: User = Depends(get_current_user)):
    """Get student profile details."""
    return current_user


@router.patch("/profile", response_model=StudentResponse)
def update_profile(
    profile_in: ProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update student profile details, preferences, or add a second contact method."""
    if profile_in.full_name is not None:
        current_user.full_name = profile_in.full_name.strip()
    if profile_in.student_level is not None:
        current_user.student_level = profile_in.student_level
    if profile_in.preferences is not None:
        updated_prefs = dict(current_user.preferences)
        updated_prefs.update(profile_in.preferences)
        current_user.preferences = updated_prefs

    # Optional addition of secondary email or phone
    if profile_in.email is not None:
        norm_email = normalize_email(profile_in.email)
        existing = db.query(User).filter(User.normalized_email == norm_email, User.id != current_user.id).first()
        if existing:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered by another account.")
        current_user.email = norm_email
        current_user.normalized_email = norm_email

    if profile_in.phone is not None:
        norm_phone = normalize_phone(profile_in.phone)
        existing = db.query(User).filter(User.normalized_phone == norm_phone, User.id != current_user.id).first()
        if existing:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Phone already registered by another account.")
        current_user.phone = norm_phone
        current_user.normalized_phone = norm_phone

    db.commit()
    db.refresh(current_user)
    return current_user


def _set_session_cookie(response: Response, token: str, max_age: Optional[int] = None) -> None:
    """Set secure HttpOnly cookie for browser sessions."""
    cookie_max_age = max_age or (settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60)
    response.set_cookie(
        key="access_token",
        value=token,
        max_age=cookie_max_age,
        expires=cookie_max_age,
        httponly=True,
        samesite="lax",
        secure=settings.APP_ENV == "production",
        path="/",
    )
