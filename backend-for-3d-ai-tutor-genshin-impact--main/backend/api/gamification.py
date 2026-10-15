"""Gamification and Learning Rewards API endpoints.
Provides transparent, idempotent XP granting, quests, and achievements.
"""

from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.db.session import get_db
from backend.dependencies import get_current_user
from backend.models.user import User
from backend.schemas.gamification import (
    GamificationSummaryResponse,
    QuestResponse,
    XPRewardRequest,
    XPTransactionResponse,
)
from backend.services.learning_rewards import learning_rewards

router = APIRouter(tags=["Gamification & Rewards"])


@router.get("/gamification/summary", response_model=GamificationSummaryResponse)
def get_gamification_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve student's total XP, academic mastery level, achievements, and neutral mode status."""
    return learning_rewards.get_summary(user_id=current_user.id, db=db)


@router.get("/gamification/quests", response_model=List[QuestResponse])
def get_active_quests(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List active transparent learning quests."""
    return learning_rewards.get_quests(user_id=current_user.id, db=db)


@router.post("/gamification/reward", response_model=XPTransactionResponse)
def grant_learning_reward(
    reward_in: XPRewardRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Award learning XP with mandatory idempotency key to prevent duplicate rewards."""
    tx = learning_rewards.grant_xp(
        user_id=current_user.id,
        amount=reward_in.amount,
        category=reward_in.category,
        idempotency_key=reward_in.idempotency_key,
        description=reward_in.description,
        source_id=reward_in.source_id,
        db=db,
    )
    return tx
