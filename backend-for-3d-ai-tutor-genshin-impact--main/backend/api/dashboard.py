"""Student Dashboard API endpoint.
"""

from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.db.session import get_db
from backend.dependencies import get_current_user
from backend.models.conversation import Conversation
from backend.models.document import Document
from backend.models.material import StudyMaterial
from backend.models.quiz import Quiz, QuizAttempt
from backend.models.user import User
from backend.schemas.progress import (
    DashboardResponse,
    RecentActivityItem,
    TopicMasteryResponse,
)
from backend.schemas.quizzes import QuizResponse
from backend.services.adaptive_learning import adaptive_learning
from backend.services.quiz_generator import quiz_generator
from backend.services.recommendations import recommendations_service

router = APIRouter(tags=["Student Dashboard"])


@router.get("/dashboard", response_model=DashboardResponse)
def get_student_dashboard(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve comprehensive overview for the student dashboard.
    Handles new users gracefully with empty lists and default zero metrics.
    """
    user_id = current_user.id

    # 1. Totals
    total_docs = db.query(Document).filter(Document.owner_id == user_id).count()
    total_materials = db.query(StudyMaterial).filter(StudyMaterial.owner_id == user_id).count()

    attempts = db.query(QuizAttempt).filter(QuizAttempt.user_id == user_id).all()
    total_quizzes = len(attempts)
    avg_score = (
        round(sum(a.score for a in attempts) / total_quizzes, 1)
        if total_quizzes > 0
        else 0.0
    )

    # 2. Recents
    recent_convs = (
        db.query(Conversation)
        .filter(Conversation.owner_id == user_id)
        .order_by(Conversation.updated_at.desc())
        .limit(5)
        .all()
    )

    recent_docs = (
        db.query(Document)
        .filter(Document.owner_id == user_id)
        .order_by(Document.created_at.desc())
        .limit(5)
        .all()
    )

    recent_materials = (
        db.query(StudyMaterial)
        .filter(StudyMaterial.owner_id == user_id)
        .order_by(StudyMaterial.created_at.desc())
        .limit(5)
        .all()
    )

    recent_quizzes_db = (
        db.query(Quiz)
        .filter(Quiz.owner_id == user_id)
        .order_by(Quiz.created_at.desc())
        .limit(5)
        .all()
    )

    recent_quizzes: List[QuizResponse] = []
    for q in recent_quizzes_db:
        public_qs = quiz_generator.get_public_questions(q)
        recent_quizzes.append(
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

    # 3. Mastery topics
    top_topics_db = adaptive_learning.get_strong_topics(user_id=user_id, db=db)
    top_topics = [TopicMasteryResponse.model_validate(t) for t in top_topics_db[:5]]

    weak_topics_db = adaptive_learning.get_weak_topics(user_id=user_id, db=db)
    weak_topics = [TopicMasteryResponse.model_validate(t) for t in weak_topics_db[:5]]

    # 4. Actionable recommendations
    recommendations = recommendations_service.get_recommendations(user_id=user_id, db=db)

    # 5. Recent activity log
    recent_activities: List[RecentActivityItem] = []
    for doc in recent_docs[:3]:
        recent_activities.append(
            RecentActivityItem(
                id=f"act_doc_{doc.id}",
                activity_type="document_upload",
                title=f"Uploaded document '{doc.title or doc.original_filename}'",
                timestamp=doc.created_at,
                metadata={"file_type": doc.file_type, "status": doc.status},
            )
        )

    for att in attempts[-3:]:
        recent_activities.append(
            RecentActivityItem(
                id=f"act_att_{att.id}",
                activity_type="quiz_attempt",
                title=f"Completed quiz assessment (Score: {att.score}%)",
                timestamp=att.completed_at,
                metadata={"score": att.score},
            )
        )

    for mat in recent_materials[:3]:
        recent_activities.append(
            RecentActivityItem(
                id=f"act_mat_{mat.id}",
                activity_type="material_created",
                title=f"Generated {mat.material_type.replace('_', ' ')} for {mat.topic}",
                timestamp=mat.created_at,
                metadata={"material_type": mat.material_type},
            )
        )

    # Character tutor assignment list
    assigned_tutors = [
        {"subject": "Mathematics", "tutor_name": "Raiden Ei / Shogun", "character_id": "raiden_shogun", "element": "Electro"},
        {"subject": "Humanities", "tutor_name": "Zhongli", "character_id": "zhongli", "element": "Geo"},
        {"subject": "Biology", "tutor_name": "Barbara", "character_id": "barbara", "element": "Hydro"},
        {"subject": "Music & Communication", "tutor_name": "Furina de Fontaine", "character_id": "furina", "element": "Hydro"},
        {"subject": "General Knowledge", "tutor_name": "Tsaritsa", "character_id": "tsaritsa", "element": "Cryo"},
        {"subject": "Moral Studies", "tutor_name": "Nahida", "character_id": "nahida", "element": "Dendro"},
        {"subject": "Physics", "tutor_name": "Ganyu", "character_id": "ganyu", "element": "Cryo"},
        {"subject": "Computer Science", "tutor_name": "Keqing", "character_id": "keqing", "element": "Electro"},
        {"subject": "Chemistry", "tutor_name": "Sucrose", "character_id": "sucrose", "element": "Anemo"},
    ]
    enrolled_subjects = [t["subject"] for t in assigned_tutors]

    return DashboardResponse(
        student_name=current_user.full_name or current_user.username,
        student_id=getattr(current_user, "student_id", None) or "STU-DEMO0001",
        email=current_user.email or current_user.normalized_email,
        phone=current_user.phone or current_user.normalized_phone,
        student_level=current_user.student_level,
        total_documents=total_docs,
        total_study_materials=total_materials,
        total_quizzes_taken=total_quizzes,
        average_quiz_score=avg_score,
        enrolled_subjects=enrolled_subjects,
        assigned_tutors=assigned_tutors,
        recent_conversations=recent_convs,
        recent_documents=recent_docs,
        recent_materials=recent_materials,
        recent_quizzes=recent_quizzes,
        top_mastery_topics=top_topics,
        weak_topics=weak_topics,
        recommended_actions=recommendations,
        recent_activities=recent_activities[:8],
    )
