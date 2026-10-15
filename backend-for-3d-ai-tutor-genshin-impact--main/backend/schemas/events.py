"""Real-time event streaming and WebSocket envelope schemas.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from backend.schemas.compat import BaseModel, Field


class EventEnvelope(BaseModel):
    """Standardized event envelope for WebSocket and SSE real-time streaming."""
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_type: str = Field(..., description="Canonical event name (e.g. character.animation, speech.started)")
    schema_version: str = "1.0"
    session_id: Optional[str] = None
    correlation_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    payload: Dict[str, Any] = Field(default_factory=dict)
