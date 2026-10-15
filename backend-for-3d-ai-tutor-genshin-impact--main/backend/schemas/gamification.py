"""Gamification schemas for learning rewards, XP, quests, and achievements.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
from backend.schemas.compat import BaseModel, Field


class XPTransactionResponse(BaseModel):
    id: str
    amount: int
    category: str
    description: str
    idempotency_key: str
    created_at: datetime

    model_config = {"from_attributes": True}


class AchievementResponse(BaseModel):
    id: str
    achievement_key: str
    title: str
    description: str
    icon: Optional[str] = None
    category: str
    unlocked_at: datetime
    achievement_metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = {"from_attributes": True}


class QuestResponse(BaseModel):
    id: str
    title: str
    description: str
    target_xp: int
    current_xp: int
    is_completed: bool
    reward_badge: Optional[str] = None


class GamificationSummaryResponse(BaseModel):
    total_xp: int
    current_level: int
    level_title: str
    next_level_xp: int
    progress_percentage: float
    achievements: List[AchievementResponse]
    recent_transactions: List[XPTransactionResponse]
    neutral_mode: bool = False


class XPRewardRequest(BaseModel):
    amount: int = Field(..., ge=1, le=500, description="Amount of XP to grant")
    category: str = Field(..., description="Action category, e.g. quiz_completed")
    description: str = Field(..., description="Human-readable reason")
    idempotency_key: str = Field(..., description="Unique key preventing duplicate XP awards")
    source_id: Optional[str] = None
