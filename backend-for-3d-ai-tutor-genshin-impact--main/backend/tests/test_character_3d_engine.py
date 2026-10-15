"""Tests for 3D character rig capabilities, performance interpretation, and asset serving.
"""
from fastapi.testclient import TestClient
from backend.main import app
from backend.services.character_rigs import (
    CHARACTER_RIG_REGISTRY,
    CharacterPerformanceInterpreter,
    RigType,
    FacialControlType,
    EyeControlType,
    JawMouthControlType,
)

client = TestClient(app)


def test_all_nine_character_rig_capabilities_exist():
    """Verify all 9 characters have registered rig capabilities."""
    expected_ids = {
        "raiden_shogun",
        "zhongli",
        "barbara",
        "furina",
        "tsaritsa",
        "nahida",
        "ganyu",
        "keqing",
        "sucrose",
    }
    caps = CharacterPerformanceInterpreter.list_all_capabilities()
    assert len(caps) == 9
    found_ids = {c.character_id for c in caps}
    assert found_ids == expected_ids


def test_morph_target_models_have_exact_inspected_shapes():
    """Verify models with facial morph targets match ground truth."""
    # Nahida has English morph targets
    nahida = CHARACTER_RIG_REGISTRY["nahida"]
    assert nahida.has_facial_rig is True
    assert nahida.facial_control_type == FacialControlType.MORPH_TARGETS
    assert "Brow_Smily_L" in nahida.morph_targets
    assert "Mouth_A01" in nahida.morph_targets
    assert "Eye_Lowereyelid" in nahida.morph_targets
    assert nahida.viseme_mapping["aa"] == "Mouth_A01"

    # Furina has Japanese MMD morph targets
    furina = CHARACTER_RIG_REGISTRY["furina"]
    assert furina.has_facial_rig is True
    assert "あ" in furina.morph_targets
    assert "まばたき" in furina.morph_targets
    assert furina.viseme_mapping["aa"] == "あ"

    # Keqing has Japanese MMD morph targets and 240 bones
    keqing = CHARACTER_RIG_REGISTRY["keqing"]
    assert keqing.bone_count == 240
    assert "にっこり" in keqing.morph_targets
    assert "あ" in keqing.morph_targets

    # Sucrose has 220 bones and Japanese MMD morph targets
    sucrose = CHARACTER_RIG_REGISTRY["sucrose"]
    assert sucrose.bone_count == 220
    assert "あ" in sucrose.morph_targets

    # Ganyu has 229 bones and Japanese MMD morph targets
    ganyu = CHARACTER_RIG_REGISTRY["ganyu"]
    assert ganyu.bone_count == 229
    assert "まばたき" in ganyu.morph_targets


def test_unskinned_and_skeletal_fallbacks():
    """Verify models without morph targets use documented fallbacks."""
    # Zhongli: Skeletal only
    zhongli = CHARACTER_RIG_REGISTRY["zhongli"]
    assert zhongli.rig_type == RigType.SKELETON_ONLY
    assert zhongli.bone_count == 185
    assert zhongli.morph_targets == []
    assert zhongli.eye_controls == EyeControlType.SKELETAL_EYES
    assert zhongli.jaw_mouth_controls == JawMouthControlType.SKELETAL_TONGUE

    # Barbara: Segmented submeshes
    barbara = CHARACTER_RIG_REGISTRY["barbara"]
    assert barbara.rig_type == RigType.SEGMENTED_MESH
    assert barbara.facial_control_type == FacialControlType.SEGMENTED_MESH_TRANSFORMS
    assert barbara.eye_controls == EyeControlType.MESH_BLINK
    assert barbara.jaw_mouth_controls == JawMouthControlType.MESH_SCALE

    # Raiden Shogun: Static mesh
    raiden = CHARACTER_RIG_REGISTRY["raiden_shogun"]
    assert raiden.rig_type == RigType.STATIC_MESH
    assert raiden.has_skeleton is False
    assert raiden.morph_targets == []

    # Tsaritsa: Static mesh
    tsaritsa = CHARACTER_RIG_REGISTRY["tsaritsa"]
    assert tsaritsa.rig_type == RigType.STATIC_MESH
    assert tsaritsa.has_skeleton is False
    assert tsaritsa.morph_targets == []


def test_api_get_all_capabilities():
    """Verify GET /api/v1/tutors-capabilities returns all 9 profiles."""
    resp = client.get("/api/v1/tutors-capabilities")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 9
    assert all("model_format" in item for item in data)
    assert all("rig_type" in item for item in data)


def test_api_get_single_capability():
    """Verify GET /api/v1/tutors/{tutor_id}/capabilities."""
    resp = client.get("/api/v1/tutors/nahida/capabilities")
    assert resp.status_code == 200
    data = resp.json()
    assert data["character_id"] == "nahida"
    assert data["has_facial_rig"] is True
    assert len(data["morph_targets"]) == 47

    # Unknown character should return 404
    resp_bad = client.get("/api/v1/tutors/nonexistent_char/capabilities")
    assert resp_bad.status_code == 404


def test_api_performance_command_generation():
    """Verify POST /api/v1/tutors/{tutor_id}/performance generates valid performance."""
    resp = client.post(
        "/api/v1/tutors/furina/performance",
        params={
            "session_id": "test-session",
            "conversation_state": "speaking",
            "semantic_expression": "warm_smile",
            "text": "Let us explore the rhythm of dance and song together!",
            "duration_ms": 3000,
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["character_id"] == "furina"
    assert data["conversation_state"] == "speaking"
    assert "target_morphs" in data
    # Warm smile for Furina contains 口角上げ and 笑い
    assert data["target_morphs"].get("口角上げ", 0) > 0
    # Visemes should contain MMD visemes
    assert len(data["viseme_timeline"]) > 0
    assert data["viseme_timeline"][0]["character_morph_target"] in furina_visemes()


def furina_visemes():
    return {"あ", "い", "う", "え", "お", "ん", "ワ"}


def test_static_and_asset_serving():
    """Verify model assets and static character engine scripts are served cleanly."""
    # 1. 3D Model asset endpoint
    resp = client.get("/api/v1/tutors/nahida/assets/Avatar_YoungGirl_Catalyst_Nahida_Tex_Hair_.png")
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "image/png"

    # 2. Path traversal attack rejection
    resp_hack = client.get("/api/v1/tutors/nahida/assets/../../main.py")
    assert resp_hack.status_code in (404, 400)

    # 3. Static character engine module serving
    resp_js = client.get("/static/character_engine/CharacterPerformanceEngine.js")
    assert resp_js.status_code == 200
    assert "class CharacterPerformanceEngine" in resp_js.text


def test_all_tutors_strictly_enforce_english_communication():
    """Verify all 9 tutors are configured with English default and system directives strictly enforce English."""
    from backend.services.tutor_profiles import tutor_registry
    from backend.services.character_behavior import character_behavior

    all_tutors = tutor_registry.get_all_tutors(enabled_only=False)
    assert len(all_tutors) == 9

    for tutor in all_tutors:
        # Check schema defaults
        assert tutor.default_language == "en"
        assert "en" in tutor.supported_languages

        # Check system directive includes English requirement and bans Japanese
        directive = character_behavior.get_system_directive(tutor, student_level="high_school")
        assert "CRITICAL LANGUAGE REQUIREMENT" in directive
        assert "standard ENGLISH" in directive
        assert "Do NOT use Japanese words" in directive
