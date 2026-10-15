"""Character tutor profile and registry schemas.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from backend.schemas.compat import BaseModel, Field
from backend.schemas.animation import AnimationProfile
from backend.schemas.voice import VoiceProfile


class AgeAppropriateRules(BaseModel):
    """Safety and developmental guidelines applied to tutor responses."""
    max_complexity_tier: str = "moderate"
    tone_guardrails: List[str] = Field(default_factory=list)
    sensitive_disclosure_handling: str = "supportive_referral_to_adults"
    prohibit_simulated_consciousness: bool = True
    foster_growth_mindset: bool = True


class TutorProfile(BaseModel):
    """Centralized character tutor definition."""
    id: str = Field(..., description="Stable character ID, e.g. raiden_shogun")
    display_name: str = Field(..., description="Full display name, e.g. Raiden Ei / Shogun")
    description: str = Field(..., description="Biographical & pedagogical summary")
    supported_subjects: List[str] = Field(..., description="Assigned primary subjects")
    teaching_personality: str = Field(..., description="Teaching personality traits")
    communication_style: str = Field(..., description="Voice and delivery style")
    explanation_strategy: str = Field(..., description="Primary explanatory methodology")
    encouragement_style: str = Field(..., description="How the character motivates students")
    hint_strategy: str = Field(..., description="Socratic scaffolding and progressive hint behavior")
    quiz_behavior: str = Field(..., description="Feedback style during assessments")
    animation_profile: AnimationProfile
    voice_profile: VoiceProfile
    pronunciation_preferences: Dict[str, str] = Field(default_factory=dict)
    default_language: str = "en"
    supported_languages: List[str] = Field(default_factory=lambda: ["en"])
    age_appropriate_response_rules: AgeAppropriateRules = Field(default_factory=AgeAppropriateRules)
    avatar_asset_ref: str = Field(default="avatar_default", description="Frontend reference key for avatar graphic")
    voice_provider: str = "mock"
    voice_id: str = "default_voice"
    is_enabled: bool = True
    configuration_version: str = "1.0.0"


class TutorSummary(BaseModel):
    """Lightweight tutor summary for catalog views."""
    id: str
    display_name: str
    description: str
    supported_subjects: List[str]
    teaching_personality: str
    avatar_asset_ref: str
    is_enabled: bool
    voice_provider: str
