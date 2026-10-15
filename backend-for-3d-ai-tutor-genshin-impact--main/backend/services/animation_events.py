"""Animation state machine and character gesture dispatch engine.
Generates validated, predictable animation instructions ensuring safe fallbacks,
priority queueing, and smooth frontend state transitions.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from backend.config import settings
from backend.schemas.animation import (
    AnimationInstruction,
    AnimationStateName,
    ExpressionType,
    GestureType,
)
from backend.services.tutor_profiles import tutor_registry

logger = logging.getLogger(__name__)

# State priority levels (1 = lowest background, 5 = highest critical override)
STATE_PRIORITIES: Dict[str, int] = {
    AnimationStateName.IDLE.value: 1,
    AnimationStateName.RESTING.value: 1,
    AnimationStateName.LISTENING.value: 2,
    AnimationStateName.THINKING.value: 2,
    AnimationStateName.EXPLAINING.value: 3,
    AnimationStateName.SPEAKING.value: 3,
    AnimationStateName.DEMONSTRATING.value: 3,
    AnimationStateName.HAPPY.value: 3,
    AnimationStateName.CURIOUS.value: 3,
    AnimationStateName.ENCOURAGING.value: 3,
    AnimationStateName.GIVING_HINT.value: 4,
    AnimationStateName.WAITING_FOR_ANSWER.value: 3,
    AnimationStateName.CORRECT_ANSWER.value: 4,
    AnimationStateName.INCORRECT_ANSWER_SUPPORTIVE.value: 4,
    AnimationStateName.CELEBRATING.value: 4,
    AnimationStateName.SURPRISED.value: 4,
    AnimationStateName.CONFUSED_GENTLY.value: 3,
    AnimationStateName.CONCERNED.value: 3,
    AnimationStateName.ERROR.value: 5,
}

# Default durations before returning to baseline/idle
DEFAULT_DURATIONS_MS: Dict[str, int] = {
    AnimationStateName.IDLE.value: 0,
    AnimationStateName.LISTENING.value: 0,
    AnimationStateName.THINKING.value: 0,
    AnimationStateName.EXPLAINING.value: 0,
    AnimationStateName.SPEAKING.value: 0,
    AnimationStateName.GIVING_HINT.value: 4000,
    AnimationStateName.CORRECT_ANSWER.value: 4500,
    AnimationStateName.INCORRECT_ANSWER_SUPPORTIVE.value: 4000,
    AnimationStateName.CELEBRATING.value: 5000,
    AnimationStateName.SURPRISED.value: 3000,
    AnimationStateName.HAPPY.value: 3500,
    AnimationStateName.ERROR.value: 3000,
}


class AnimationEventService:
    """Manages character animation state transitions, gesture mapping, and event validation."""

    @classmethod
    def create_instruction(
        cls,
        state: str | AnimationStateName,
        character_id: str,
        session_id: Optional[str] = None,
        reason: Optional[str] = None,
        custom_expression: Optional[str] = None,
        custom_gesture: Optional[str] = None,
        intensity: Optional[float] = None,
        correlation_id: Optional[str] = None,
    ) -> AnimationInstruction:
        """Create a validated AnimationInstruction with guaranteed fallback."""
        state_str = state.value if isinstance(state, AnimationStateName) else str(state)

        # 1. Validate state name or fallback to idle
        valid_states = {s.value for s in AnimationStateName}
        if state_str not in valid_states:
            logger.warning(f"Unknown animation state '{state_str}'. Falling back to 'idle'.")
            state_str = AnimationStateName.IDLE.value

        # 2. Retrieve character profile for asset keys
        profile = tutor_registry.get_tutor_by_id(character_id)
        anim_profile = profile.animation_profile if profile else None

        # 3. Derive asset key
        anim_key = cls._resolve_animation_key(state_str, anim_profile)

        # 4. Resolve semantic expression & gesture
        expression, gesture = cls._resolve_expression_and_gesture(state_str, custom_expression, custom_gesture)

        # 5. Determine duration and looping
        duration_ms = DEFAULT_DURATIONS_MS.get(state_str, 3000)
        is_looping = state_str in (
            AnimationStateName.IDLE.value,
            AnimationStateName.LISTENING.value,
            AnimationStateName.THINKING.value,
            AnimationStateName.EXPLAINING.value,
            AnimationStateName.SPEAKING.value,
            AnimationStateName.RESTING.value,
        )

        # 6. Intensity clamping
        configured_intensity = (
            intensity
            if intensity is not None
            else (anim_profile.default_intensity if anim_profile else settings.ANIMATION_INTENSITY_DEFAULT)
        )
        clamped_intensity = max(0.1, min(1.0, float(configured_intensity)))

        priority = STATE_PRIORITIES.get(state_str, 2)
        event_id = correlation_id or f"anim_{uuid.uuid4().hex[:12]}"

        return AnimationInstruction(
            state=state_str,
            character_id=character_id,
            expression=expression,
            gesture=gesture,
            animation_key=anim_key,
            intensity=clamped_intensity,
            transition="smooth",
            duration_ms=duration_ms,
            is_looping=is_looping,
            priority=priority,
            reason=reason or f"Transition to {state_str}",
            session_id=session_id,
            event_id=event_id,
            timestamp=datetime.now(timezone.utc),
        )

    @classmethod
    def _resolve_animation_key(cls, state: str, anim_profile: Optional[Any]) -> str:
        """Resolve character animation key with guaranteed safe fallback."""
        if not anim_profile:
            return "idle_default"

        if state == AnimationStateName.IDLE.value:
            return anim_profile.default_idle_key
        elif state in (AnimationStateName.EXPLAINING.value, AnimationStateName.SPEAKING.value):
            return anim_profile.explaining_keys[0] if anim_profile.explaining_keys else anim_profile.fallback_key
        elif state == AnimationStateName.LISTENING.value:
            return anim_profile.listening_keys[0] if anim_profile.listening_keys else anim_profile.fallback_key
        elif state == AnimationStateName.THINKING.value:
            return anim_profile.thinking_keys[0] if anim_profile.thinking_keys else anim_profile.fallback_key
        elif state in (AnimationStateName.CELEBRATING.value, AnimationStateName.CORRECT_ANSWER.value, AnimationStateName.HAPPY.value):
            return anim_profile.celebrating_keys[0] if anim_profile.celebrating_keys else anim_profile.fallback_key
        elif state == AnimationStateName.GIVING_HINT.value:
            return anim_profile.hint_keys[0] if anim_profile.hint_keys else anim_profile.fallback_key
        elif state == AnimationStateName.INCORRECT_ANSWER_SUPPORTIVE.value:
            return anim_profile.supportive_keys[0] if anim_profile.supportive_keys else anim_profile.fallback_key
        elif state == AnimationStateName.ERROR.value:
            return anim_profile.fallback_key
        return anim_profile.fallback_key

    @classmethod
    def _resolve_expression_and_gesture(
        cls,
        state: str,
        custom_expression: Optional[str],
        custom_gesture: Optional[str],
    ) -> tuple[str, str]:
        """Map validated state to natural facial expression and semantic gesture."""
        if custom_expression and custom_gesture:
            return custom_expression, custom_gesture

        expr = ExpressionType.NEUTRAL.value
        gest = GestureType.NONE.value

        if state == AnimationStateName.IDLE.value:
            expr = ExpressionType.NEUTRAL.value
            gest = GestureType.GENTLE_ACKNOWLEDGMENT.value
        elif state == AnimationStateName.LISTENING.value:
            expr = ExpressionType.FOCUSED.value
            gest = GestureType.LISTENING_ATTENTIVELY.value
        elif state == AnimationStateName.THINKING.value:
            expr = ExpressionType.PENSIVE.value
            gest = GestureType.THINKING_POSE.value
        elif state in (AnimationStateName.EXPLAINING.value, AnimationStateName.SPEAKING.value):
            expr = ExpressionType.CONFIDENT.value
            gest = GestureType.POINT_FORWARD.value
        elif state == AnimationStateName.GIVING_HINT.value:
            expr = ExpressionType.REASSURING.value
            gest = GestureType.CURIOUS_HEAD_TILT.value
        elif state in (AnimationStateName.CORRECT_ANSWER.value, AnimationStateName.CELEBRATING.value):
            expr = ExpressionType.EXCITED.value
            gest = GestureType.CELEBRATING_GESTURE.value
        elif state == AnimationStateName.INCORRECT_ANSWER_SUPPORTIVE.value:
            expr = ExpressionType.EMPATHETIC.value
            gest = GestureType.ENCOURAGING_THUMBS_UP.value
        elif state == AnimationStateName.DEMONSTRATING.value:
            expr = ExpressionType.CONFIDENT.value
            gest = GestureType.DEMONSTRATION_GESTURE.value
        elif state == AnimationStateName.WAITING_FOR_ANSWER.value:
            expr = ExpressionType.REASSURING.value
            gest = GestureType.GENTLE_NOD.value
        elif state == AnimationStateName.ERROR.value:
            expr = ExpressionType.GENTLE_CONCERN.value
            gest = GestureType.GENTLE_ACKNOWLEDGMENT.value

        return custom_expression or expr, custom_gesture or gest


# Global singleton instance
animation_service = AnimationEventService()
