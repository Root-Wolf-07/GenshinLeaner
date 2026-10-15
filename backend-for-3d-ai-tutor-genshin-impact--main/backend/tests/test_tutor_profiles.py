"""Automated tests for Character Tutor Registry and Profile specifications.
Verifies all 9 characters, subject specializations, and profile schemas.
"""

from fastapi.testclient import TestClient
from backend.services.tutor_profiles import tutor_registry

CORE_CHARACTERS = [
    ("raiden_shogun", "Raiden Ei / Shogun", "Mathematics"),
    ("zhongli", "Zhongli", "History"),
    ("barbara", "Barbara", "Biology"),
    ("furina", "Furina", "Music"),
    ("tsaritsa", "Tsaritsa", "Languages"),
    ("nahida", "Nahida", "Moral Studies"),
    ("ganyu", "Ganyu", "Physics"),
    ("keqing", "Keqing", "Computer Science"),
    ("sucrose", "Sucrose", "Chemistry"),
]


def test_all_nine_character_profiles_registered():
    """Requirement 1 & 2: All 9 core character profiles must be registered and active."""
    all_tutors = tutor_registry.get_all_tutors()
    assert len(all_tutors) >= 9

    registered_ids = {t.id for t in all_tutors}
    for char_id, display_name, subject in CORE_CHARACTERS:
        assert char_id in registered_ids
        profile = tutor_registry.get_tutor_by_id(char_id)
        assert profile is not None
        assert profile.is_enabled is True
        assert len(profile.supported_subjects) > 0
        assert profile.teaching_personality != ""
        assert profile.communication_style != ""
        assert profile.explanation_strategy != ""
        assert profile.animation_profile is not None
        assert profile.voice_profile is not None


def test_subject_mapping_enforcement():
    """Requirement 2: Every assigned subject correctly maps to the expected character."""
    for char_id, display_name, primary_subject in CORE_CHARACTERS:
        tutor = tutor_registry.get_tutor_for_subject(primary_subject)
        assert tutor is not None, f"No tutor found for subject {primary_subject}"
        assert tutor.id == char_id
        assert tutor_registry.validate_tutor_subject(char_id, primary_subject) is True


def test_unsupported_subject_handling():
    """Requirement 4: Unsupported subject selections must be rejected safely."""
    # Raiden is Math, not Biology
    assert tutor_registry.validate_tutor_subject("raiden_shogun", "Biology") is False
    # Sucrose is Chemistry, not History
    assert tutor_registry.validate_tutor_subject("sucrose", "History") is False


def test_tutors_catalog_endpoint(client: TestClient):
    """API endpoint GET /api/v1/tutors returns valid character summaries."""
    res = client.get("/api/v1/tutors")
    assert res.status_code == 200
    data = res.json()
    assert len(data) >= 9
    ids = [t["id"] for t in data]
    assert "raiden_shogun" in ids
    assert "zhongli" in ids
    assert "barbara" in ids


def test_tutors_detail_endpoint(client: TestClient):
    """API endpoint GET /api/v1/tutors/{tutor_id} returns full profile."""
    res = client.get("/api/v1/tutors/keqing")
    assert res.status_code == 200
    data = res.json()
    assert data["id"] == "keqing"
    assert data["display_name"] == "Keqing"
    assert "Computer Science" in data["supported_subjects"]
    assert "animation_profile" in data
    assert "voice_profile" in data


def test_unknown_tutor_rejected(client: TestClient):
    """Requirement 3: Unknown characters are safely rejected with 404."""
    res = client.get("/api/v1/tutors/non_existent_character")
    assert res.status_code == 404
    assert "not found" in res.json()["error"]["message"].lower()
