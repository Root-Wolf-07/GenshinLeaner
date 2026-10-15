"""Quiz Grader Service.
Evaluates submitted student answers on the backend, generates detailed feedback,
and records attempts.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Union
from backend.db.session import Session

from backend.models.quiz import Quiz, QuizAttempt
from backend.schemas.chat import Citation
from backend.schemas.quizzes import QuizSubmitRequest, QuizResultResponse, QuizGradedItem
from backend.services.adaptive_learning import adaptive_learning
from backend.services.learning_rewards import learning_rewards

logger = logging.getLogger(__name__)


class QuizGraderService:
    """Grades quizzes securely on backend and updates topic mastery."""

    @classmethod
    def grade_submission(
        cls,
        quiz: Quiz,
        submission: QuizSubmitRequest,
        user_id: str,
        db: Session,
    ) -> QuizResultResponse:
        """Score objective and free-response questions and record attempt."""
        user_answers = submission.answers
        graded_items: List[QuizGradedItem] = []

        total_points = 0.0
        earned_points = 0.0

        topic_stats: Dict[str, Dict[str, int]] = {}

        for q in quiz.questions:
            q_id = str(q.get("id"))
            prompt = q.get("prompt", "")
            q_type = q.get("question_type", "multiple_choice")
            correct_ans = q.get("correct_answer")
            explanation = q.get("explanation", "")
            points_possible = float(q.get("points", 1.0))
            topic_tag = q.get("topic_tag", quiz.topic)

            total_points += points_possible

            student_ans = user_answers.get(q_id)
            is_correct, score_fraction, feedback = cls._evaluate_answer(q_type, student_ans, correct_ans)

            item_points = points_possible * score_fraction
            earned_points += item_points

            # Track stats per topic
            if topic_tag not in topic_stats:
                topic_stats[topic_tag] = {"correct": 0, "total": 0}
            topic_stats[topic_tag]["total"] += 1
            if is_correct:
                topic_stats[topic_tag]["correct"] += 1

            # Format question citations
            citations = [Citation(**c) for c in q.get("citations", [])]

            graded_items.append(
                QuizGradedItem(
                    question_id=q_id,
                    prompt=prompt,
                    question_type=q_type,
                    user_answer=student_ans,
                    correct_answer=correct_ans,
                    is_correct=is_correct,
                    score=item_points,
                    points_possible=points_possible,
                    explanation=explanation,
                    feedback=feedback,
                    citations=citations,
                )
            )

        # Calculate final percentage
        percentage = round((earned_points / total_points) * 100.0, 1) if total_points > 0 else 0.0
        passed = percentage >= 70.0

        # Overall summary feedback
        if percentage >= 90:
            summary_feedback = "Outstanding mastery! You demonstrated deep comprehension of the concepts."
        elif percentage >= 75:
            summary_feedback = "Great work! You have a solid grasp, with just a few areas for refinement."
        elif percentage >= 60:
            summary_feedback = "Good foundation, but targeted revision on weak concepts is recommended."
        else:
            summary_feedback = "This topic requires closer review. Revisit the lecture notes and review step-by-step examples."

        # Persist QuizAttempt record
        attempt_id = str(uuid.uuid4())
        attempt = QuizAttempt(
            id=attempt_id,
            quiz_id=quiz.id,
            user_id=user_id,
            submitted_answers=user_answers,
            graded_results=[item.model_dump() for item in graded_items],
            score=percentage,
            total_points=total_points,
            earned_points=earned_points,
            completed_at=datetime.now(timezone.utc),
        )
        db.add(attempt)
        db.commit()

        # Update topic mastery for each tested topic
        for t_tag, stats in topic_stats.items():
            adaptive_learning.update_topic_mastery(
                user_id=user_id,
                topic=t_tag,
                correct_count=stats["correct"],
                total_count=stats["total"],
                difficulty=quiz.difficulty,
                db=db,
            )

        # Award learning XP and check achievements idempotently
        earned_xp = int(50 + (earned_points / max(1.0, total_points)) * 25)
        learning_rewards.grant_xp(
            user_id=user_id,
            amount=earned_xp,
            category="quiz_completed",
            idempotency_key=f"quiz_attempt_{attempt_id}",
            description=f"Completed quiz on {quiz.topic} (Score: {percentage}%)",
            source_id=quiz.id,
            db=db,
        )
        if passed:
            learning_rewards.unlock_achievement(user_id=user_id, achievement_key="quiz_master_70", db=db)

        return QuizResultResponse(
            attempt_id=attempt_id,
            quiz_id=quiz.id,
            score=percentage,
            earned_points=earned_points,
            total_points=total_points,
            passed=passed,
            summary_feedback=summary_feedback,
            graded_items=graded_items,
            completed_at=attempt.completed_at,
        )

    @classmethod
    def _evaluate_answer(
        cls,
        q_type: str,
        student_ans: Optional[Union[str, bool]],
        correct_ans: Union[str, bool],
    ) -> tuple[bool, float, str]:
        """Grade a single question and generate pedagogical feedback."""
        if student_ans is None:
            return False, 0.0, "No answer provided."

        # 1. True / False
        if q_type == "true_false":
            s_val = str(student_ans).strip().lower() in ("true", "1", "yes")
            c_val = str(correct_ans).strip().lower() in ("true", "1", "yes")
            is_correct = (s_val == c_val)
            feedback = "Correct identification." if is_correct else "Incorrect. Review the underlying premise."
            return is_correct, 1.0 if is_correct else 0.0, feedback

        # 2. Multiple Choice
        if q_type == "multiple_choice":
            s_clean = str(student_ans).strip().lower()
            c_clean = str(correct_ans).strip().lower()
            is_correct = (s_clean == c_clean)
            feedback = "Spot on!" if is_correct else f"Incorrect. The correct option is '{correct_ans}'."
            return is_correct, 1.0 if is_correct else 0.0, feedback

        # 3. Fill in the blank / Short answer
        s_text = str(student_ans).strip().lower()
        c_text = str(correct_ans).strip().lower()

        if s_text == c_text:
            return True, 1.0, "Exact match! Excellent formulation."

        # Keyword overlap evaluation
        c_words = set(re.findall(r"\w+", c_text))
        s_words = set(re.findall(r"\w+", s_text))

        if not c_words:
            return False, 0.0, "Incorrect."

        overlap = len(c_words.intersection(s_words)) / len(c_words)
        if overlap >= 0.75:
            return True, 1.0, "Accurate and well-articulated explanation."
        elif overlap >= 0.40:
            return True, 0.7, f"Partially correct. Key aspects were captured, but compare with: '{correct_ans}'."
        else:
            return False, 0.0, f"Needs improvement. Recommended answer: '{correct_ans}'."


# Global instance
quiz_grader = QuizGraderService()
