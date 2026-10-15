"""Recommendations Service.
Generates transparent, rule-grounded study recommendations based on actual stored user activity.
"""

from __future__ import annotations

import logging
from typing import List
from backend.db.session import Session

from backend.models.document import Document
from backend.models.learning import TopicMastery
from backend.models.quiz import Quiz, QuizAttempt
from backend.schemas.progress import RecommendationItem

logger = logging.getLogger(__name__)


class RecommendationsService:
    """Produces actionable recommendations based on real progress metrics."""

    @staticmethod
    def get_recommendations(user_id: str, db: Session) -> List[RecommendationItem]:
        """Analyze stored quiz attempts and topic masteries to formulate suggestions."""
        recommendations: List[RecommendationItem] = []

        # 1. Check for weak topics (< 65% mastery)
        weak_topics = (
            db.query(TopicMastery)
            .filter(TopicMastery.user_id == user_id, TopicMastery.mastery_score < 65.0)
            .order_by(TopicMastery.mastery_score.asc())
            .limit(3)
            .all()
        )

        for wt in weak_topics:
            recommendations.append(
                RecommendationItem(
                    id=f"rec_weak_{wt.id}",
                    action_type="review_topic",
                    title=f"Strengthen Weak Area: {wt.topic}",
                    description=f"Your current mastery estimate in {wt.topic} is {wt.mastery_score}% across {wt.total_questions_attempted} questions.",
                    reasoning=f"Repeated incorrect responses ({wt.incorrect_answers} errors) indicate a conceptual gap.",
                    target_topic=wt.topic,
                    priority="high",
                )
            )
            recommendations.append(
                RecommendationItem(
                    id=f"rec_flash_{wt.id}",
                    action_type="generate_flashcards",
                    title=f"Generate Flashcards for {wt.topic}",
                    description=f"Active recall flashcards will help solidify core definitions and formulas for {wt.topic}.",
                    reasoning="Flashcards optimize spaced repetition for topics with lower retention.",
                    target_topic=wt.topic,
                    priority="medium",
                )
            )

        # 2. Check for recent failed quiz attempts (< 70% score) to suggest re-takes
        failed_attempts = (
            db.query(QuizAttempt)
            .filter(QuizAttempt.user_id == user_id, QuizAttempt.score < 70.0)
            .order_by(QuizAttempt.completed_at.desc())
            .limit(2)
            .all()
        )

        for fa in failed_attempts:
            quiz = db.query(Quiz).filter(Quiz.id == fa.quiz_id).first()
            if quiz:
                recommendations.append(
                    RecommendationItem(
                        id=f"rec_retake_{fa.id}",
                        action_type="retake_quiz",
                        title=f"Retake Assessment: {quiz.title}",
                        description=f"You scored {fa.score}% on your last attempt. Review the explanations and retake the quiz.",
                        reasoning="Testing after review produces a 50% increase in long-term retention.",
                        target_quiz_id=quiz.id,
                        target_topic=quiz.topic,
                        priority="medium",
                    )
                )

        # 3. Check for available uploaded documents that haven't been quizzed yet
        quizzed_topics = {
            t[0].lower()
            for t in db.query(TopicMastery.topic).filter(TopicMastery.user_id == user_id).all()
        }
        untested_docs = (
            db.query(Document)
            .filter(Document.owner_id == user_id, Document.status == "ready")
            .limit(5)
            .all()
        )

        for doc in untested_docs:
            doc_title = doc.title or doc.original_filename
            if doc_title.lower() not in quizzed_topics and doc.chunk_count > 0:
                recommendations.append(
                    RecommendationItem(
                        id=f"rec_doc_{doc.id}",
                        action_type="revisit_document",
                        title=f"Explore Material: {doc_title}",
                        description=f"Generate study notes or practice questions from '{doc_title}' ({doc.page_count or doc.slide_count or 1} pages/slides).",
                        reasoning="Applying active learning to uploaded course slides enhances lecture recall.",
                        target_document_id=doc.id,
                        target_page_number=1,
                        priority="low",
                    )
                )
                break

        # 4. If new user with no activity, provide clear starting guidance
        if not recommendations:
            recommendations.append(
                RecommendationItem(
                    id="rec_start_doc",
                    action_type="revisit_document",
                    title="Upload Your First Course Document",
                    description="Upload lecture slides (PDF/PPTX) or class notes to unlock grounded tutoring and personalized quizzes.",
                    reasoning="The AI Study Companion uses your actual course material to ensure accurate, citation-verified learning.",
                    priority="high",
                )
            )
            recommendations.append(
                RecommendationItem(
                    id="rec_start_quiz",
                    action_type="review_topic",
                    title="Take an Initial Diagnostic Quiz",
                    description="Generate a 5-question quiz on your primary subject to gauge your starting mastery level.",
                    reasoning="Initial diagnostics establish baseline topic mastery metrics.",
                    priority="medium",
                )
            )

        return recommendations


# Global instance
recommendations_service = RecommendationsService()
