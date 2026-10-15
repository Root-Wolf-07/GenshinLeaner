"""Adaptive Learning and Topic Mastery Service.
Tracks student topic performance, computes weighted mastery metrics, and identifies knowledge gaps.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional
from backend.db.session import Session

from backend.models.learning import TopicMastery

logger = logging.getLogger(__name__)


class AdaptiveLearningService:
    """Computes mastery estimates and identifies weak areas transparently."""

    @staticmethod
    def update_topic_mastery(
        user_id: str,
        topic: str,
        correct_count: int,
        total_count: int,
        difficulty: str,
        db: Session,
    ) -> TopicMastery:
        """Update or create topic mastery record following a quiz attempt."""
        clean_topic = topic.strip().title()

        mastery = (
            db.query(TopicMastery)
            .filter(
                TopicMastery.user_id == user_id,
                TopicMastery.topic == clean_topic,
            )
            .first()
        )

        if not mastery:
            mastery = TopicMastery(
                id=str(uuid.uuid4()),
                user_id=user_id,
                topic=clean_topic,
                total_questions_attempted=0,
                correct_answers=0,
                incorrect_answers=0,
                mastery_score=50.0,
                difficulty_level=difficulty,
                last_practiced_at=datetime.now(timezone.utc),
            )
            db.add(mastery)

        # Increment counts
        mastery.total_questions_attempted += total_count
        mastery.correct_answers += correct_count
        mastery.incorrect_answers += (total_count - correct_count)
        mastery.difficulty_level = difficulty
        mastery.last_practiced_at = datetime.now(timezone.utc)

        # Transparent adaptive formula:
        # 1. Base empirical accuracy
        base_accuracy = (
            (mastery.correct_answers / mastery.total_questions_attempted) * 100.0
            if mastery.total_questions_attempted > 0
            else 50.0
        )

        # 2. Difficulty modifier
        diff_weights = {"beginner": 0.92, "intermediate": 1.0, "advanced": 1.08}
        weight = diff_weights.get(difficulty.lower(), 1.0)
        adjusted_score = base_accuracy * weight

        # 3. Confidence smoothing for low sample sizes (Bayesian prior toward 50%)
        sample_size = mastery.total_questions_attempted
        k = 5.0  # prior weight
        prior_mean = 50.0
        smoothed = (sample_size * adjusted_score + k * prior_mean) / (sample_size + k)

        # Clamp between 0.0 and 100.0
        mastery.mastery_score = round(max(0.0, min(100.0, smoothed)), 1)

        db.commit()
        db.refresh(mastery)
        return mastery

    @staticmethod
    def get_weak_topics(user_id: str, db: Session, threshold: float = 65.0) -> List[TopicMastery]:
        """Find topics with low mastery scores requiring targeted review."""
        return (
            db.query(TopicMastery)
            .filter(
                TopicMastery.user_id == user_id,
                TopicMastery.mastery_score < threshold,
            )
            .order_by(TopicMastery.mastery_score.asc())
            .all()
        )

    @staticmethod
    def get_strong_topics(user_id: str, db: Session, threshold: float = 75.0) -> List[TopicMastery]:
        """Find mastered topics."""
        return (
            db.query(TopicMastery)
            .filter(
                TopicMastery.user_id == user_id,
                TopicMastery.mastery_score >= threshold,
            )
            .order_by(TopicMastery.mastery_score.desc())
            .all()
        )

    @staticmethod
    def get_all_topics(user_id: str, db: Session) -> List[TopicMastery]:
        """Get all topics for user."""
        return (
            db.query(TopicMastery)
            .filter(TopicMastery.user_id == user_id)
            .order_by(TopicMastery.last_practiced_at.desc())
            .all()
        )


# Global instance
adaptive_learning = AdaptiveLearningService()
