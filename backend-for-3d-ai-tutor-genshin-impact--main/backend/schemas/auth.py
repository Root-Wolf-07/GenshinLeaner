"""Authentication and Student Profile Pydantic Schemas.
Data contracts for registration, email/phone verification, password recovery,
session authentication, and personal student profile updates.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional
from backend.schemas.compat import BaseModel, EmailStr, Field


class StudentRegister(BaseModel):
    """Payload for registering a new student account."""
    full_name: str = Field(..., min_length=1, max_length=255, description="Student's real or preferred name")
    identifier: str = Field(..., min_length=3, max_length=255, description="Email address or phone number")
    channel: Optional[str] = Field("email", description="Registration identifier type: 'email' or 'phone'")
    password: str = Field(..., min_length=8, max_length=128, description="Private student password (min 8 chars)")
    confirm_password: str = Field(..., min_length=8, max_length=128, description="Password confirmation")
    terms_accepted: bool = Field(..., description="Consent to Terms of Service & Privacy Policy")
    student_level: Optional[str] = Field("undergraduate", description="Academic level (middle_school, high_school, undergraduate, graduate, professional)")

    # Legacy/compatibility alias
    username: Optional[str] = None
    email: Optional[str] = None


# Backward-compatibility alias
UserRegister = StudentRegister


class StudentLogin(BaseModel):
    """Payload for student login."""
    identifier: str = Field(..., min_length=3, max_length=255, description="Email address, phone number, or username")
    password: str = Field(..., min_length=1, max_length=128, description="Account password")
    remember_me: bool = Field(False, description="Persist session for extended duration")

    # Compatibility with older endpoints
    username_or_email: Optional[str] = None


# Backward-compatibility alias
UserLogin = StudentLogin


class VerifyCodeRequest(BaseModel):
    """Payload to verify an OTP registration or activation code."""
    identifier: str = Field(..., min_length=3, max_length=255, description="Email or phone number")
    code: str = Field(..., min_length=4, max_length=10, description="Verification code (e.g. 6-digit OTP)")


class ResendCodeRequest(BaseModel):
    """Payload to request a new verification OTP."""
    identifier: str = Field(..., min_length=3, max_length=255, description="Email or phone number")


class ForgotPasswordRequest(BaseModel):
    """Payload to request a password reset code/token."""
    identifier: str = Field(..., min_length=3, max_length=255, description="Registered email or phone number")


class ResetPasswordRequest(BaseModel):
    """Payload to set a new password using a verified reset code."""
    identifier: str = Field(..., min_length=3, max_length=255, description="Registered email or phone number")
    code: str = Field(..., min_length=4, max_length=64, description="Password reset code or token")
    new_password: str = Field(..., min_length=8, max_length=128, description="New secure password")
    confirm_password: str = Field(..., min_length=8, max_length=128, description="Confirm new password")


class StudentResponse(BaseModel):
    """Public student account representation, including permanent Student ID."""
    id: str
    student_id: str
    full_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    username: str
    student_level: str
    preferences: Dict[str, Any]
    is_active: bool
    is_verified: bool
    created_at: datetime
    updated_at: datetime
    last_login_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# Backward-compatibility alias
UserResponse = StudentResponse


class AuthSessionToken(BaseModel):
    """Standardized authentication response returning JWT token and student record."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: StudentResponse


# Backward-compatibility alias
Token = AuthSessionToken


class ProfileUpdate(BaseModel):
    """Payload for updating student profile settings and preferences."""
    full_name: Optional[str] = None
    student_level: Optional[str] = None
    preferences: Optional[Dict[str, Any]] = None
    phone: Optional[str] = None
    email: Optional[str] = None
