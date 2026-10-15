"""Interactive Character Tutor Session Orchestrator.
Coordinates character persona, Socratic intent routing, RAG retrieval, citation verification,
animation state instructions, and voice synthesis.
"""

from __future__ import annotations

import json
import logging
import re
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from backend.config import settings
from backend.models.document import Document
from backend.models.tutor_session import TutorSession, TutorSessionMessage
from backend.schemas.animation import AnimationInstruction, AnimationStateName
from backend.schemas.chat import Citation
from backend.schemas.tutor_session import (
    TutorMessageRequest,
    TutorMessageResponse,
    TutorSessionCreateRequest,
    TutorSessionDetailResponse,
    TutorSessionSummaryResponse,
    TutorSessionUpdateRequest,
    SessionCancelResponse,
)
from backend.schemas.voice import SpeechResponse
from backend.services.animation_events import animation_service
from backend.services.character_behavior import character_behavior
from backend.services.citation_validator import citation_validator
from backend.services.learning_rewards import learning_rewards
from backend.services.llm_provider import get_llm_provider
from backend.services.retriever import retriever_service, RetrievedPassage
from backend.services.text_to_speech import tts_service
from backend.services.tutor_profiles import tutor_registry
from backend.services.voice_service import voice_service
from backend.services.character_rigs import CharacterPerformanceInterpreter

logger = logging.getLogger(__name__)


class InteractiveSessionService:
    """Manages active interactive tutor sessions, message cycles, and intent handling."""

    @classmethod
    def create_session(
        cls,
        request: TutorSessionCreateRequest,
        user_id: str,
        db: Session,
    ) -> TutorSession:
        """Create and persist a new interactive tutor session with validated character and subject."""
        # 1. Validate tutor existence
        tutor = tutor_registry.get_tutor_by_id(request.tutor_id)
        if not tutor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Character tutor '{request.tutor_id}' is not recognized.",
            )

        # 2. Validate subject eligibility
        if not tutor_registry.validate_tutor_subject(request.tutor_id, request.subject):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Tutor '{tutor.display_name}' does not specialize in '{request.subject}'. "
                    f"Specialized subjects: {', '.join(tutor.supported_subjects)}"
                ),
            )

        # 3. Create session record
        session_id = str(uuid.uuid4())
        session_title = request.title or f"{tutor.display_name} - {request.subject} Studio"

        session = TutorSession(
            id=session_id,
            user_id=user_id,
            tutor_id=tutor.id,
            subject=request.subject,
            title=session_title,
            interaction_mode=request.interaction_mode or "multimodal",
            student_level=request.student_level or "undergraduate",
            difficulty=request.difficulty or "intermediate",
            language=request.language or "en",
            source_mode=request.source_mode or "both",
            selected_document_ids=request.selected_document_ids or [],
            preferences=request.preferences or {},
            session_metadata={},
            status="active",
        )
        db.add(session)
        db.commit()
        db.refresh(session)
        return session

    @classmethod
    def get_session(cls, session_id: str, user_id: str, db: Session) -> TutorSession:
        """Retrieve a session enforcing ownership isolation."""
        session = (
            db.query(TutorSession)
            .filter(TutorSession.id == session_id, TutorSession.user_id == user_id)
            .first()
        )
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tutor session not found or access denied.",
            )
        return session

    @classmethod
    def update_session(
        cls,
        session_id: str,
        update_data: TutorSessionUpdateRequest,
        user_id: str,
        db: Session,
    ) -> TutorSession:
        """Update session settings."""
        session = cls.get_session(session_id, user_id, db)
        if update_data.title is not None:
            session.title = update_data.title
        if update_data.interaction_mode is not None:
            session.interaction_mode = update_data.interaction_mode
        if update_data.difficulty is not None:
            session.difficulty = update_data.difficulty
        if update_data.language is not None:
            session.language = update_data.language
        if update_data.source_mode is not None:
            session.source_mode = update_data.source_mode
        if update_data.selected_document_ids is not None:
            session.selected_document_ids = update_data.selected_document_ids
        if update_data.preferences is not None:
            session.preferences = update_data.preferences

        db.commit()
        db.refresh(session)
        return session

    @classmethod
    def cancel_session(cls, session_id: str, user_id: str, db: Session) -> SessionCancelResponse:
        """Halt active speech and mark session cancelled."""
        session = cls.get_session(session_id, user_id, db)
        session.status = "cancelled"
        db.commit()

        # Halt background audio scheduling
        tts_service.cancel_speech(session_id=session_id)

        return SessionCancelResponse(
            session_id=session_id,
            status="cancelled",
            message=f"Session with tutor {session.tutor_id} cancelled.",
            audio_cancelled=True,
        )

    @classmethod
    def process_message(
        cls,
        session_id: str,
        request: TutorMessageRequest,
        user_id: str,
        db: Session,
    ) -> TutorMessageResponse:
        """Process incoming student message, execute cognitive cycle, and format response."""
        session = cls.get_session(session_id, user_id, db)
        tutor = tutor_registry.get_tutor_by_id(session.tutor_id)
        if not tutor:
            raise HTTPException(status_code=500, detail="Character profile corrupted.")

        # 1. RAG Retrieval if enabled and documents available
        passages: List[RetrievedPassage] = []
        insufficient_evidence = False
        allowed_docs = session.selected_document_ids

        if allowed_docs:
            valid_docs = db.query(Document.id).filter(
                Document.id.in_(allowed_docs), Document.owner_id == user_id
            ).all()
            allowed_docs = [d[0] for d in valid_docs]

        if session.source_mode in ("uploaded", "both"):
            passages = retriever_service.retrieve(
                user_id=user_id,
                query=request.content,
                db=db,
                allowed_document_ids=allowed_docs if allowed_docs else None,
                top_k=5,
            )
            if session.source_mode == "uploaded" and not passages:
                insufficient_evidence = True

        # 2. Determine pedagogical mode & animation state according to student intent
        anim_state = AnimationStateName.EXPLAINING
        anim_reason = f"Responding to {request.intent}"
        intent = request.intent
        pedagogical_mode = "socratic_adaptive_scaffolding"

        intent_instruction = ""
        if intent == "explain_simply":
            intent_instruction = "Explain this concept in ultra-simple, intuitive terms using accessible everyday analogies."
            anim_state = AnimationStateName.DEMONSTRATING
        elif intent == "explain_in_detail":
            intent_instruction = "Provide a deep, rigorous breakdown detailing foundational axioms, edge cases, and mathematical derivations."
            anim_state = AnimationStateName.EXPLAINING
        elif intent == "show_example":
            intent_instruction = "Present a clear, worked concrete example demonstrating every step of the solution."
            anim_state = AnimationStateName.DEMONSTRATING
        elif intent == "give_hint":
            hint_level = request.hint_level or 1
            intent_instruction = character_behavior.format_progressive_hint(tutor, session.subject, hint_level)
            anim_state = AnimationStateName.GIVING_HINT
            pedagogical_mode = f"progressive_hint_level_{hint_level}"
        elif intent == "check_my_answer":
            intent_instruction = (
                f"Evaluate the student's submitted answer: '{request.user_answer_submission or request.content}'. "
                "Point out what is correct first. If incorrect or incomplete, provide supportive guidance and a hint."
            )
            anim_state = AnimationStateName.WAITING_FOR_ANSWER
        elif intent == "practice_question":
            intent_instruction = "Generate 1 targeted conceptual practice problem to verify student comprehension."
            anim_state = AnimationStateName.CURIOUS
        elif intent == "summarize_topic":
            intent_instruction = "Summarize the key takeaways and core formulas for this topic in concise bullet points."
            anim_state = AnimationStateName.EXPLAINING
        elif intent == "repeat_explanation":
            intent_instruction = "Rephrase the previous explanation from a fresh angle with alternative metaphors."
            anim_state = AnimationStateName.EXPLAINING

        # Handle strict uploaded mode missing evidence
        if insufficient_evidence:
            content = (
                f"I searched through your uploaded study materials for {session.subject}, but could not find sufficient "
                "verified evidence to answer this question accurately.\n\n"
                "Please upload relevant lecture notes or switch the source mode to 'both' or 'general'."
            )
            anim_instr = animation_service.create_instruction(
                state=AnimationStateName.CONFUSED_GENTLY,
                character_id=tutor.id,
                session_id=session.id,
                reason="Insufficient evidence in uploaded notes",
            )
            # Persist messages
            cls._persist_messages(session.id, request.content, intent, content, [], anim_instr, None, db)
            return TutorMessageResponse(
                message_id=str(uuid.uuid4()),
                session_id=session.id,
                role="assistant",
                content=content,
                intent=intent,
                tutor_id=tutor.id,
                character_name=tutor.display_name,
                animation=anim_instr,
                speech=None,
                citations=[],
                suggested_follow_ups=["Switch to general knowledge mode", "Upload supplementary lecture notes"],
                insufficient_evidence=True,
                pedagogical_mode="evidence_limitation",
                created_at=datetime.now(timezone.utc),
            )

        # 3. Construct System Prompt combining Character Persona and Directives
        system_prompt = character_behavior.get_system_directive(tutor, session.student_level)
        if intent_instruction:
            system_prompt += f"\nINTERACTION DIRECTIVE: {intent_instruction}\n"

        prompt_blocks = [f"Student Inquiry: {request.content}\n"]
        if passages:
            prompt_blocks.append("Retrieved Ground-Truth Evidence from Course Materials:\n")
            for p in passages:
                loc = f"Page {p.page_number}" if p.page_number else (f"Slide {p.slide_number}" if p.slide_number else "Section")
                prompt_blocks.append(
                    f'<DOCUMENT_EVIDENCE chunk_id="{p.chunk_id}" source="{p.document_title}" location="{loc}">\n'
                    f"{p.content}\n"
                    f"</DOCUMENT_EVIDENCE>\n"
                )
            prompt_blocks.append(
                "\nCite supporting evidence references. At the end, output:\n"
                "```json_citations\n"
                '[{"citation_id": "chunk_id", "excerpt": "exact phrase"}]\n'
                "```\n"
            )

        provider = get_llm_provider()
        raw_output = provider.generate(
            prompt="\n".join(prompt_blocks),
            system_prompt=system_prompt,
            temperature=0.3,
        )

        # 4. Extract and Validate Citations
        citations: List[Citation] = []
        clean_text = raw_output

        cit_match = re.search(r"```json_citations\s*([\s\S]*?)\s*```", raw_output)
        if cit_match:
            try:
                raw_cits = json.loads(cit_match.group(1))
                if isinstance(raw_cits, list):
                    citations = citation_validator.validate_citations_list(
                        raw_cits, user_id=user_id, db=db, allowed_document_ids=allowed_docs
                    )
            except Exception as e:
                logger.warning(f"Citation parsing error: {e}")
            clean_text = raw_output[: cit_match.start()].strip()
        else:
            if passages and session.source_mode in ("uploaded", "both"):
                primary = passages[0]
                val = citation_validator.validate_citation(
                    {"citation_id": primary.chunk_id, "excerpt": primary.content[:160]},
                    user_id=user_id,
                    db=db,
                    allowed_document_ids=allowed_docs,
                )
                if val:
                    citations.append(val)

        # 5. Build Animation Instruction
        anim_instruction = animation_service.create_instruction(
            state=anim_state,
            character_id=tutor.id,
            session_id=session.id,
            reason=anim_reason,
        )

        # 6. Generate Voice Audio if requested or mode is voice/multimodal
        speech_resp: Optional[SpeechResponse] = None
        should_voice = (
            request.request_voice
            if request.request_voice is not None
            else (session.interaction_mode in ("voice_only", "multimodal"))
        )

        if should_voice:
            try:
                speech_resp = voice_service.synthesize_response(
                    text=clean_text,
                    tutor_id=tutor.id,
                    user_id=user_id,
                    db=db,
                    session_id=session.id,
                )
            except Exception as e:
                logger.warning(f"Voice generation skipped due to error: {e}")
                speech_resp = None

        # 7. Build 3D Performance Command
        semantic_expr = (
            "warm_smile" if anim_state in ("happy", "celebrating") else (
                "thoughtful" if anim_state in ("thinking", "giving_hint") else (
                    "curious" if anim_state == "curious" else "explaining"
                )
            )
        )
        performance_cmd = CharacterPerformanceInterpreter.build_performance_command(
            character_id=tutor.id,
            session_id=session.id,
            conversation_state="speaking",
            semantic_expression=semantic_expr,
            text=clean_text,
            duration_ms=speech_resp.duration_ms if speech_resp else 2500,
            priority=anim_instruction.priority,
        )

        # 8. Grant Transparent Learning XP (idempotently)
        msg_id = str(uuid.uuid4())
        learning_rewards.grant_xp(
            user_id=user_id,
            amount=15,
            category="question_answered",
            idempotency_key=f"tutor_msg_{msg_id}",
            description=f"Engaged with tutor {tutor.display_name} on {session.subject}",
            db=db,
        )

        # 9. Follow-ups
        follow_ups = [
            f"Can you provide another worked example?",
            f"Give me a progressive hint on how to practice this.",
            f"Test my understanding with a practice question.",
        ]

        # 10. Persist Messages
        cls._persist_messages(
            session.id,
            request.content,
            intent,
            clean_text,
            citations,
            anim_instruction,
            speech_resp.audio_id if speech_resp else None,
            db,
        )

        return TutorMessageResponse(
            message_id=msg_id,
            session_id=session.id,
            role="assistant",
            content=clean_text,
            intent=intent,
            tutor_id=tutor.id,
            character_name=tutor.display_name,
            animation=anim_instruction,
            performance=performance_cmd,
            speech=speech_resp,
            citations=citations,
            suggested_follow_ups=follow_ups,
            insufficient_evidence=False,
            pedagogical_mode=pedagogical_mode,
            created_at=datetime.now(timezone.utc),
        )

    @classmethod
    def _persist_messages(
        cls,
        session_id: str,
        user_content: str,
        intent: str,
        assistant_content: str,
        citations: List[Citation],
        anim_instruction: AnimationInstruction,
        audio_id: Optional[str],
        db: Session,
    ) -> None:
        # Serialize pydantic models to JSON-safe dictionaries (datetimes to ISO strings)
        citations_data = [json.loads(c.model_dump_json()) for c in citations] if citations else []
        anim_data = json.loads(anim_instruction.model_dump_json()) if anim_instruction else {}

        u_msg = TutorSessionMessage(
            session_id=session_id,
            role="user",
            content=user_content,
            intent=intent,
            citations=[],
            animation_state={},
            audio_id=None,
            message_metadata={},
        )
        a_msg = TutorSessionMessage(
            session_id=session_id,
            role="assistant",
            content=assistant_content,
            intent=intent,
            citations=citations_data,
            animation_state=anim_data,
            audio_id=audio_id,
            message_metadata={},
        )
        db.add(u_msg)
        db.add(a_msg)
        db.commit()


# Global singleton instance
interactive_sessions = InteractiveSessionService()
