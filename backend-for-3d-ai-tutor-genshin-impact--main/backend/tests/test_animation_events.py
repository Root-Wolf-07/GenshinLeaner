"""Automated tests for Animation State Engine.
Verifies state machine transitions, priority ordering, gesture resolution, and fallback safety.
"""

from backend.schemas.animation import AnimationStateName, ExpressionType, GestureType
from backend.services.animation_events import animation_service


def test_valid_animation_instruction_generation():
    """Requirement 8: Valid animation instructions conform to schema with character asset keys."""
    instr = animation_service.create_instruction(
        state=AnimationStateName.EXPLAINING,
        character_id="raiden_shogun",
        session_id="session_123",
        reason="Explaining matrix algebra",
    )
    assert instr.state == "explaining"
    assert instr.character_id == "raiden_shogun"
    assert instr.session_id == "session_123"
    assert "raiden" in instr.animation_key
    assert instr.expression == ExpressionType.CONFIDENT.value
    assert instr.gesture == GestureType.POINT_FORWARD.value
    assert 0.0 <= instr.intensity <= 1.0
    assert instr.priority >= 2


def test_unknown_animation_state_safe_fallback():
    """Requirement 8: Unrecognized or corrupted state safely falls back to 'idle'."""
    instr = animation_service.create_instruction(
        state="completely_unknown_state_xyz",
        character_id="zhongli",
    )
    assert instr.state == "idle"
    assert instr.animation_key == "zhongli_idle_dignified"
    assert instr.expression == ExpressionType.NEUTRAL.value


def test_animation_intensity_clamping():
    """Animation intensity must be clamped between 0.1 and 1.0 for accessibility."""
    # Test lower bound
    instr_low = animation_service.create_instruction(
        state=AnimationStateName.HAPPY,
        character_id="barbara",
        intensity=-0.5,
    )
    assert instr_low.intensity == 0.1

    # Test upper bound
    instr_high = animation_service.create_instruction(
        state=AnimationStateName.CELEBRATING,
        character_id="furina",
        intensity=2.5,
    )
    assert instr_high.intensity == 1.0


def test_animation_priority_ordering():
    """Requirement 9: High-priority states (error, celebration) override lower-priority states."""
    idle = animation_service.create_instruction(AnimationStateName.IDLE, "ganyu")
    hint = animation_service.create_instruction(AnimationStateName.GIVING_HINT, "ganyu")
    err = animation_service.create_instruction(AnimationStateName.ERROR, "ganyu")

    assert err.priority > hint.priority
    assert hint.priority > idle.priority


def test_character_specific_gestures():
    """Verify semantic gestures for question answering and encouragement."""
    correct_instr = animation_service.create_instruction(
        state=AnimationStateName.CORRECT_ANSWER,
        character_id="sucrose",
    )
    assert correct_instr.gesture == GestureType.CELEBRATING_GESTURE.value
    assert correct_instr.expression == ExpressionType.EXCITED.value

    support_instr = animation_service.create_instruction(
        state=AnimationStateName.INCORRECT_ANSWER_SUPPORTIVE,
        character_id="nahida",
    )
    assert support_instr.gesture == GestureType.ENCOURAGING_THUMBS_UP.value
    assert support_instr.expression == ExpressionType.EMPATHETIC.value
