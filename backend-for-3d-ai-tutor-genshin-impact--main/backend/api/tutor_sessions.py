"""Tutor Sessions and Interactive Character Messaging API endpoints.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.db.session import get_db
from backend.dependencies import get_current_user
from backend.models.tutor_session import TutorSession
from backend.models.user import User
from backend.schemas.animation import AnimationInstruction
from backend.schemas.chat import Citation
from backend.schemas.tutor_session import (
    SessionCancelResponse,
    TutorMessageRequest,
    TutorMessageResponse,
    TutorSessionCreateRequest,
    TutorSessionDetailResponse,
    TutorSessionSummaryResponse,
    TutorSessionUpdateRequest,
)
from backend.services.interactive_sessions import interactive_sessions
from backend.services.tutor_profiles import tutor_registry

router = APIRouter(tags=["Tutor Sessions"])


@router.post("/tutor-sessions", response_model=TutorSessionSummaryResponse, status_code=status.HTTP_201_CREATED)
def create_tutor_session(
    request: TutorSessionCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new interactive session with a selected character tutor and subject."""
    session = interactive_sessions.create_session(request=request, user_id=current_user.id, db=db)
    return session


@router.get("/tutor-sessions", response_model=List[TutorSessionSummaryResponse])
def list_tutor_sessions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all interactive tutor sessions for the authenticated student."""
    return (
        db.query(TutorSession)
        .filter(TutorSession.user_id == current_user.id)
        .order_by(TutorSession.updated_at.desc())
        .all()
    )


@router.get("/tutor-sessions/{session_id}", response_model=TutorSessionDetailResponse)
def get_tutor_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve full session detail including message history, animation states, and citations."""
    session = interactive_sessions.get_session(session_id=session_id, user_id=current_user.id, db=db)
    tutor = tutor_registry.get_tutor_by_id(session.tutor_id)
    char_name = tutor.display_name if tutor else session.tutor_id

    # Format messages
    formatted_messages = []
    for m in session.messages:
        citations = [Citation(**c) for c in m.citations] if m.citations else []
        anim_data = m.animation_state or {}
        if not anim_data.get("character_id"):
            anim_data["character_id"] = session.tutor_id
        anim = AnimationInstruction(**anim_data) if anim_data else AnimationInstruction(character_id=session.tutor_id)

        formatted_messages.append(
            TutorMessageResponse(
                message_id=m.id,
                session_id=session.id,
                role=m.role,
                content=m.content,
                intent=m.intent or "ask_question",
                tutor_id=session.tutor_id,
                character_name=char_name,
                animation=anim,
                speech=None,
                citations=citations,
                suggested_follow_ups=[],
                insufficient_evidence=False,
                pedagogical_mode="standard",
                created_at=m.created_at,
            )
        )

    return TutorSessionDetailResponse(
        id=session.id,
        user_id=session.user_id,
        tutor_id=session.tutor_id,
        subject=session.subject,
        title=session.title,
        interaction_mode=session.interaction_mode,
        status=session.status,
        difficulty=session.difficulty,
        language=session.language,
        source_mode=session.source_mode,
        selected_document_ids=session.selected_document_ids,
        preferences=session.preferences,
        created_at=session.created_at,
        updated_at=session.updated_at,
        messages=formatted_messages,
    )


@router.patch("/tutor-sessions/{session_id}", response_model=TutorSessionSummaryResponse)
def update_tutor_session(
    session_id: str,
    update_data: TutorSessionUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update ongoing session parameters (mode, difficulty, language, selected documents)."""
    return interactive_sessions.update_session(
        session_id=session_id, update_data=update_data, user_id=current_user.id, db=db
    )


@router.post("/tutor-sessions/{session_id}/messages", response_model=TutorMessageResponse)
def send_message_to_tutor(
    session_id: str,
    request: TutorMessageRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Send student inquiry or typed interaction intent to the character tutor."""
    return interactive_sessions.process_message(
        session_id=session_id, request=request, user_id=current_user.id, db=db
    )


@router.post("/tutor-sessions/{session_id}/cancel", response_model=SessionCancelResponse)
def cancel_tutor_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Interrupt/cancel active tutor response or active voice playback."""
    return interactive_sessions.cancel_session(
        session_id=session_id, user_id=current_user.id, db=db
    )
