"""Real-time WebSocket and event streaming for interactive character tutoring.
Dispatches character animation instructions, speech coordination, and learning events.
"""

import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Dict, Set
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, status

from backend.db.session import SessionLocal
from backend.dependencies import decode_access_token, DEMO_USER_ID
from backend.models.tutor_session import TutorSession
from backend.schemas.events import EventEnvelope
from backend.schemas.tutor_session import TutorMessageRequest
from backend.services.interactive_sessions import interactive_sessions

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Interactive Real-Time Events"])

# Connection registry: session_id -> Set of active WebSockets
_ACTIVE_CONNECTIONS: Dict[str, Set[WebSocket]] = {}


class ConnectionManager:
    """Manages active WebSockets with room/session scoping and authentication."""

    @classmethod
    async def connect(cls, session_id: str, websocket: WebSocket) -> None:
        await websocket.accept()
        if session_id not in _ACTIVE_CONNECTIONS:
            _ACTIVE_CONNECTIONS[session_id] = set()
        _ACTIVE_CONNECTIONS[session_id].add(websocket)

    @classmethod
    def disconnect(cls, session_id: str, websocket: WebSocket) -> None:
        if session_id in _ACTIVE_CONNECTIONS:
            _ACTIVE_CONNECTIONS[session_id].discard(websocket)
            if not _ACTIVE_CONNECTIONS[session_id]:
                del _ACTIVE_CONNECTIONS[session_id]

    @classmethod
    async def broadcast_to_session(cls, session_id: str, envelope: EventEnvelope) -> None:
        """Broadcast event envelope to all connected clients for a session."""
        sockets = _ACTIVE_CONNECTIONS.get(session_id, set()).copy()
        msg_json = envelope.model_dump_json()
        dead_sockets = set()
        for ws in sockets:
            try:
                await ws.send_text(msg_json)
            except Exception:
                dead_sockets.add(ws)
        for ws in dead_sockets:
            cls.disconnect(session_id, ws)


@router.websocket("/ws/tutor-sessions/{session_id}")
async def tutor_session_websocket(
    websocket: WebSocket,
    session_id: str,
    token: str = Query(default=""),
):
    """Real-time bidirectional WebSocket connection for character animation, speech cues, and interactive questions."""
    db = SessionLocal()
    try:
        # 1. Authenticate user from query token or demo fallback
        user_id = DEMO_USER_ID
        if token:
            payload = decode_access_token(token)
            if payload and payload.get("sub"):
                user_id = payload["sub"]

        # 2. Verify session ownership
        session = (
            db.query(TutorSession)
            .filter(TutorSession.id == session_id, TutorSession.user_id == user_id)
            .first()
        )
        if not session:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Unauthorized or session not found")
            return

        # 3. Register connection
        await ConnectionManager.connect(session_id, websocket)

        # 4. Emit initial state event
        welcome_event = EventEnvelope(
            event_type="tutor.state_changed",
            session_id=session_id,
            payload={
                "state": "idle",
                "character_id": session.tutor_id,
                "message": f"Connected to {session.tutor_id} session.",
            },
        )
        await websocket.send_text(welcome_event.model_dump_json())

        # 5. Event loop
        while True:
            data = await websocket.receive_text()
            if len(data) > 32768:
                err_event = EventEnvelope(
                    event_type="operation.error",
                    session_id=session_id,
                    payload={"error": "Payload exceeds 32KB limit"},
                )
                await websocket.send_text(err_event.model_dump_json())
                continue

            try:
                payload = json.loads(data)
            except json.JSONDecodeError:
                err_event = EventEnvelope(
                    event_type="operation.error",
                    session_id=session_id,
                    payload={"error": "Invalid JSON envelope"},
                )
                await websocket.send_text(err_event.model_dump_json())
                continue

            action = payload.get("action", "message")

            if action == "message":
                content = payload.get("content", "")
                intent = payload.get("intent", "ask_question")
                if not content:
                    continue

                # Broadcast thinking animation
                thinking_event = EventEnvelope(
                    event_type="character.animation",
                    session_id=session_id,
                    payload={
                        "state": "thinking",
                        "character_id": session.tutor_id,
                        "intensity": 0.8,
                    },
                )
                await ConnectionManager.broadcast_to_session(session_id, thinking_event)

                # Execute interaction in thread/service
                req = TutorMessageRequest(content=content, intent=intent)
                resp = interactive_sessions.process_message(
                    session_id=session_id, request=req, user_id=user_id, db=db
                )

                # Broadcast tutor message started
                start_event = EventEnvelope(
                    event_type="tutor.message.started",
                    session_id=session_id,
                    payload={"message_id": resp.message_id, "character_id": session.tutor_id},
                )
                await ConnectionManager.broadcast_to_session(session_id, start_event)

                # Broadcast character animation instruction
                anim_event = EventEnvelope(
                    event_type="character.animation",
                    session_id=session_id,
                    payload=resp.animation.model_dump(),
                )
                await ConnectionManager.broadcast_to_session(session_id, anim_event)

                # Broadcast 3D character performance command if present
                if resp.performance:
                    perf_event = EventEnvelope(
                        event_type="character.performance",
                        session_id=session_id,
                        payload=resp.performance.model_dump(),
                    )
                    await ConnectionManager.broadcast_to_session(session_id, perf_event)

                # Broadcast citations if present
                if resp.citations:
                    cit_event = EventEnvelope(
                        event_type="tutor.citation.available",
                        session_id=session_id,
                        payload={"citations": [c.model_dump() for c in resp.citations]},
                    )
                    await ConnectionManager.broadcast_to_session(session_id, cit_event)

                # Broadcast speech playback cues if generated
                if resp.speech:
                    speech_event = EventEnvelope(
                        event_type="speech.started",
                        session_id=session_id,
                        payload=resp.speech.model_dump(),
                    )
                    await ConnectionManager.broadcast_to_session(session_id, speech_event)

                # Broadcast completed message
                completed_event = EventEnvelope(
                    event_type="tutor.message.completed",
                    session_id=session_id,
                    payload=resp.model_dump(),
                )
                await ConnectionManager.broadcast_to_session(session_id, completed_event)

            elif action in ("cancel", "interrupt"):
                interactive_sessions.cancel_session(session_id=session_id, user_id=user_id, db=db)
                cancel_event = EventEnvelope(
                    event_type="speech.cancelled",
                    session_id=session_id,
                    payload={"session_id": session_id, "status": "cancelled", "reason": action},
                )
                await ConnectionManager.broadcast_to_session(session_id, cancel_event)

            elif action == "listen_start":
                # Student began speaking -> transition tutor immediately to listening
                listen_event = EventEnvelope(
                    event_type="character.animation",
                    session_id=session_id,
                    payload={
                        "state": "listening",
                        "character_id": session.tutor_id,
                        "expression": "neutral_attentive",
                        "gesture": "listening_attentively",
                        "intensity": 0.8,
                    },
                )
                await ConnectionManager.broadcast_to_session(session_id, listen_event)

    except WebSocketDisconnect:
        ConnectionManager.disconnect(session_id, websocket)
    except Exception as e:
        logger.error(f"WebSocket session error: {e}")
        ConnectionManager.disconnect(session_id, websocket)
    finally:
        db.close()
