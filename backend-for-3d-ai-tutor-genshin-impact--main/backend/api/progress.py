"""Learning Progress Analytics API endpoints.
"""

from typing import Any, Dict, List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.db.session import get_db
from backend.dependencies import get_current_user
from backend.models.quiz import QuizAttempt
from backend.models.user import User
from backend.schemas.progress import (
    ProgressResponse,
    TopicMasteryResponse,
)
from backend.schemas.quizzes import AttemptResponse
from backend.services.adaptive_learning import adaptive_learning

router = APIRouter(tags=["Learning Progress & Analytics"])


@router.get("/progress", response_model=ProgressResponse)
def get_overall_progress(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve detailed learning progress, accuracy over time, and topic mastery."""
    user_id = current_user.id

    # 1. Gather all attempts
    attempts = (
        db.query(QuizAttempt)
        .filter(QuizAttempt.user_id == user_id)
        .order_by(QuizAttempt.completed_at.asc())
        .all()
    )

    total_quizzes = len(attempts)
    total_earned = sum(a.earned_points for a in attempts)
    total_possible = sum(a.total_points for a in attempts)

    overall_accuracy = (
        round((total_earned / total_possible) * 100.0, 1)
        if total_possible > 0
        else 0.0
    )

    total_questions = sum(len(a.graded_results) for a in attempts)
    total_correct = sum(
        sum(1 for item in a.graded_results if item.get("is_correct"))
        for a in attempts
    )

    # 2. Topic breakdowns
    all_topics_db = adaptive_learning.get_all_topics(user_id=user_id, db=db)
    all_topics = [TopicMasteryResponse.model_validate(t) for t in all_topics_db]

    weak_topics_db = adaptive_learning.get_weak_topics(user_id=user_id, db=db)
    weak_topics = [TopicMasteryResponse.model_validate(t) for t in weak_topics_db]

    strong_topics_db = adaptive_learning.get_strong_topics(user_id=user_id, db=db)
    strong_topics = [TopicMasteryResponse.model_validate(t) for t in strong_topics_db]

    # 3. Accuracy timeline improvements
    recent_improvements: List[Dict[str, Any]] = []
    if len(attempts) >= 2:
        prev_score = attempts[-2].score
        latest_score = attempts[-1].score
        delta = round(latest_score - prev_score, 1)
        recent_improvements.append({
            "metric": "Recent Quiz Score Trend",
            "delta": delta,
            "previous_score": prev_score,
            "latest_score": latest_score,
            "trend": "improving" if delta >= 0 else "declining",
        })

    # 4. Revision targets
    targets = [t.topic for t in weak_topics[:4]]
    if not targets and all_topics:
        targets = [all_topics[0].topic]

    return ProgressResponse(
        overall_accuracy=overall_accuracy,
        total_quizzes_taken=total_quizzes,
        total_questions_answered=total_questions,
        total_correct=total_correct,
        weakest_topics=weak_topics[:5],
        strongest_topics=strong_topics[:5],
        topic_breakdown=all_topics,
        recent_improvements=recent_improvements,
        suggested_revision_targets=targets,
    )


@router.get("/progress/topics", response_model=List[TopicMasteryResponse])
def get_topic_masteries(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve granular topic-level mastery metrics."""
    topics = adaptive_learning.get_all_topics(user_id=current_user.id, db=db)
    return topics


@router.get("/progress/history", response_model=List[AttemptResponse])
def get_attempt_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve student's full quiz assessment attempt history."""
    return (
        db.query(QuizAttempt)
        .filter(QuizAttempt.user_id == current_user.id)
        .order_by(QuizAttempt.completed_at.desc())
        .all()
    )
