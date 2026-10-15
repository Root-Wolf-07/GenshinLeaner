"""Adaptive Quiz and Assessment API endpoints.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.db.session import get_db
from backend.dependencies import get_current_user
from backend.models.quiz import Quiz, QuizAttempt
from backend.models.user import User
from backend.schemas.quizzes import (
    QuizGenerateRequest,
    QuizResponse,
    QuizSubmitRequest,
    QuizResultResponse,
    AttemptResponse,
)
from backend.services.quiz_generator import quiz_generator
from backend.services.quiz_grader import quiz_grader

router = APIRouter(tags=["Quizzes & Assessments"])


@router.post("/quizzes/generate", response_model=QuizResponse, status_code=status.HTTP_201_CREATED)
def generate_quiz(
    request: QuizGenerateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Generate an adaptive quiz with questions grounded in course materials or subject concepts."""
    quiz = quiz_generator.generate_quiz(request=request, user_id=current_user.id, db=db)
    public_questions = quiz_generator.get_public_questions(quiz)

    return QuizResponse(
        id=quiz.id,
        owner_id=quiz.owner_id,
        title=quiz.title,
        topic=quiz.topic,
        difficulty=quiz.difficulty,
        student_level=quiz.student_level,
        source_mode=quiz.source_mode,
        document_ids=quiz.document_ids,
        total_questions=quiz.total_questions,
        questions=public_questions,
        created_at=quiz.created_at,
    )


@router.get("/quizzes", response_model=List[QuizResponse])
def list_quizzes(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List quizzes created for the student with answer keys securely redacted."""
    quizzes = (
        db.query(Quiz)
        .filter(Quiz.owner_id == current_user.id)
        .order_by(Quiz.created_at.desc())
        .all()
    )

    results: List[QuizResponse] = []
    for q in quizzes:
        public_qs = quiz_generator.get_public_questions(q)
        results.append(
            QuizResponse(
                id=q.id,
                owner_id=q.owner_id,
                title=q.title,
                topic=q.topic,
                difficulty=q.difficulty,
                student_level=q.student_level,
                source_mode=q.source_mode,
                document_ids=q.document_ids,
                total_questions=q.total_questions,
                questions=public_qs,
                created_at=q.created_at,
            )
        )
    return results


@router.get("/quizzes/{quiz_id}", response_model=QuizResponse)
def get_quiz(
    quiz_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get quiz for student. Correct answers are kept private until submission."""
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id, Quiz.owner_id == current_user.id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found.")

    public_questions = quiz_generator.get_public_questions(quiz)
    return QuizResponse(
        id=quiz.id,
        owner_id=quiz.owner_id,
        title=quiz.title,
        topic=quiz.topic,
        difficulty=quiz.difficulty,
        student_level=quiz.student_level,
        source_mode=quiz.source_mode,
        document_ids=quiz.document_ids,
        total_questions=quiz.total_questions,
        questions=public_questions,
        created_at=quiz.created_at,
    )


@router.post("/quizzes/{quiz_id}/submit", response_model=QuizResultResponse)
def submit_quiz(
    quiz_id: str,
    submission: QuizSubmitRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Submit student answers for backend grading, explanation reveal, and mastery updates."""
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id, Quiz.owner_id == current_user.id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found.")

    return quiz_grader.grade_submission(
        quiz=quiz,
        submission=submission,
        user_id=current_user.id,
        db=db,
    )


@router.get("/quizzes/{quiz_id}/attempts", response_model=List[AttemptResponse])
def get_quiz_attempts(
    quiz_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """View past attempts and scores for a specific quiz."""
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id, Quiz.owner_id == current_user.id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found.")

    return (
        db.query(QuizAttempt)
        .filter(QuizAttempt.quiz_id == quiz_id, QuizAttempt.user_id == current_user.id)
        .order_by(QuizAttempt.completed_at.desc())
        .all()
    )


@router.get("/quizzes/attempts/{attempt_id}", response_model=AttemptResponse)
def get_single_attempt(
    attempt_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """View detailed results and feedback for a past attempt."""
    attempt = (
        db.query(QuizAttempt)
        .filter(QuizAttempt.id == attempt_id, QuizAttempt.user_id == current_user.id)
        .first()
    )
    if not attempt:
        raise HTTPException(status_code=404, detail="Quiz attempt not found.")
    return attempt
