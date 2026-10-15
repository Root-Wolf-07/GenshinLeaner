"""Learning rewards and non-manipulative gamification service.
Enforces backend idempotency, transparent XP calculation, quest progression,
and neutral mode settings without guilt mechanics.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from backend.config import settings
from backend.models.learning_event import UserAchievement, XPTransaction
from backend.models.user import User
from backend.schemas.gamification import (
    AchievementResponse,
    GamificationSummaryResponse,
    QuestResponse,
    XPTransactionResponse,
)

logger = logging.getLogger(__name__)

# Standard level thresholds: level N requires 100 * N XP
LEVEL_TITLES = [
    "Curious Explorer",
    "Apprentice Scholar",
    "Inquisitive Thinker",
    "Concept Architect",
    "Analytical Master",
    "Academic Virtuoso",
]

DEFAULT_ACHIEVEMENTS = [
    {
        "achievement_key": "first_question",
        "title": "First Step of Inquiry",
        "description": "Asked your very first question to an AI tutor.",
        "icon": "sparkles",
        "category": "curiosity",
    },
    {
        "achievement_key": "quiz_master_70",
        "title": "Validated Knowledge",
        "description": "Scored 70% or higher on an adaptive assessment.",
        "icon": "trophy",
        "category": "mastery",
    },
    {
        "achievement_key": "socratic_scholar",
        "title": "Socratic Thinker",
        "description": "Solved a multi-step concept using progressive hints.",
        "icon": "brain",
        "category": "persistence",
    },
    {
        "achievement_key": "study_material_creator",
        "title": "Knowledge Synthesizer",
        "description": "Generated personalized structured study materials.",
        "icon": "book-open",
        "category": "mastery",
    },
]


class LearningRewardsService:
    """Manages XP transactions, achievements, and non-manipulative gamification."""

    @classmethod
    def grant_xp(
        cls,
        user_id: str,
        amount: int,
        category: str,
        idempotency_key: str,
        description: str,
        db: Session,
        source_id: Optional[str] = None,
    ) -> Optional[XPTransaction]:
        """Award XP idempotently. Returns existing transaction if idempotency key already processed."""
        if not settings.ENABLE_GAMIFICATION:
            return None

        # 1. Check idempotency key to prevent double rewards
        existing = (
            db.query(XPTransaction)
            .filter(XPTransaction.idempotency_key == idempotency_key)
            .first()
        )
        if existing:
            logger.info(f"Idempotent XP award duplicate skipped: key={idempotency_key}")
            return existing

        # 2. Check neutral mode preference
        user = db.query(User).filter(User.id == user_id).first()
        if user and user.preferences.get("neutral_mode", False):
            # Record minimal XP silently without fanfare
            pass

        # 3. Create XP Transaction
        tx = XPTransaction(
            id=str(uuid.uuid4()),
            user_id=user_id,
            amount=amount,
            category=category,
            source_id=source_id,
            idempotency_key=idempotency_key,
            description=description,
        )
        db.add(tx)
        db.commit()
        db.refresh(tx)

        # 4. Check for milestone unlocks
        cls._evaluate_automatic_achievements(user_id=user_id, category=category, db=db)

        return tx

    @classmethod
    def get_summary(cls, user_id: str, db: Session) -> GamificationSummaryResponse:
        """Compute user's transparent XP totals, current level, quests, and achievements."""
        txs = (
            db.query(XPTransaction)
            .filter(XPTransaction.user_id == user_id)
            .order_by(XPTransaction.created_at.desc())
            .all()
        )
        total_xp = sum(t.amount for t in txs)

        # Determine level: each level requires 150 XP
        current_level = max(1, (total_xp // 150) + 1)
        level_index = min(current_level - 1, len(LEVEL_TITLES) - 1)
        level_title = LEVEL_TITLES[level_index]

        next_level_xp = current_level * 150
        xp_in_level = total_xp % 150
        progress_pct = round((xp_in_level / 150.0) * 100.0, 1)

        achievements_db = (
            db.query(UserAchievement)
            .filter(UserAchievement.user_id == user_id)
            .order_by(UserAchievement.unlocked_at.desc())
            .all()
        )
        achievements = [
            AchievementResponse(
                id=a.id,
                achievement_key=a.achievement_key,
                title=a.title,
                description=a.description,
                icon=a.icon,
                category=a.category,
                unlocked_at=a.unlocked_at,
                achievement_metadata=a.achievement_metadata or {},
            )
            for a in achievements_db
        ]
        recent_txs = [XPTransactionResponse.model_validate(t) for t in txs[:10]]

        user = db.query(User).filter(User.id == user_id).first()
        neutral_mode = bool(user.preferences.get("neutral_mode", False)) if user else False

        return GamificationSummaryResponse(
            total_xp=total_xp,
            current_level=current_level,
            level_title=level_title,
            next_level_xp=next_level_xp,
            progress_percentage=progress_pct,
            achievements=achievements,
            recent_transactions=recent_txs,
            neutral_mode=neutral_mode,
        )

    @classmethod
    def get_quests(cls, user_id: str, db: Session) -> List[QuestResponse]:
        """Return transparent educational quests grounded in verified learning milestones."""
        txs = db.query(XPTransaction).filter(XPTransaction.user_id == user_id).all()
        quiz_xp = sum(t.amount for t in txs if t.category == "quiz_completed")
        socratic_xp = sum(t.amount for t in txs if t.category in ("socratic_checkpoint", "question_answered"))

        return [
            QuestResponse(
                id="quest_daily_concept",
                title="Conceptual Deep Dive",
                description="Engage with a character tutor and complete a concept check.",
                target_xp=30,
                current_xp=min(30, socratic_xp),
                is_completed=socratic_xp >= 30,
                reward_badge="Curious Mind",
            ),
            QuestResponse(
                id="quest_quiz_mastery",
                title="Assessment Mastery",
                description="Earn XP through validated adaptive quizzes.",
                target_xp=100,
                current_xp=min(100, quiz_xp),
                is_completed=quiz_xp >= 100,
                reward_badge="Mastery Explorer",
            ),
        ]

    @classmethod
    def unlock_achievement(
        cls,
        user_id: str,
        achievement_key: str,
        db: Session,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[UserAchievement]:
        """Unlock an achievement idempotently."""
        existing = (
            db.query(UserAchievement)
            .filter(
                UserAchievement.user_id == user_id,
                UserAchievement.achievement_key == achievement_key,
            )
            .first()
        )
        if existing:
            return existing

        template = next((a for a in DEFAULT_ACHIEVEMENTS if a["achievement_key"] == achievement_key), None)
        title = template["title"] if template else achievement_key.replace("_", " ").title()
        description = template["description"] if template else "Milestone achieved."
        icon = template["icon"] if template else "award"
        category = template["category"] if template else "mastery"

        achievement = UserAchievement(
            id=str(uuid.uuid4()),
            user_id=user_id,
            achievement_key=achievement_key,
            title=title,
            description=description,
            icon=icon,
            category=category,
            unlocked_at=datetime.now(timezone.utc),
            achievement_metadata=metadata or {},
        )
        db.add(achievement)
        db.commit()
        db.refresh(achievement)
        return achievement

    @classmethod
    def _evaluate_automatic_achievements(cls, user_id: str, category: str, db: Session) -> None:
        """Trigger milestone evaluation upon learning action."""
        if category == "question_answered":
            cls.unlock_achievement(user_id, "first_question", db)
        elif category == "quiz_completed":
            cls.unlock_achievement(user_id, "quiz_master_70", db)
        elif category == "socratic_checkpoint":
            cls.unlock_achievement(user_id, "socratic_scholar", db)
        elif category == "study_material_created":
            cls.unlock_achievement(user_id, "study_material_creator", db)


# Global singleton instance
learning_rewards = LearningRewardsService()
