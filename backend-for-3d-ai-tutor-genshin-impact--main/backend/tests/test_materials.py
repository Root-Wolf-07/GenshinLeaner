"""Automated tests for Study Material Studio.
"""

from fastapi.testclient import TestClient


def test_generate_study_notes(client: TestClient):
    payload = {
        "topic": "Hash Tables and Collision Resolution",
        "material_type": "study_notes",
        "student_level": "undergraduate",
        "difficulty": "intermediate",
        "source_mode": "general",
    }
    response = client.post("/api/v1/materials/generate", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["topic"] == "Hash Tables and Collision Resolution"
    assert data["material_type"] == "study_notes"
    assert "raw_markdown" in data
    assert len(data["raw_markdown"]) > 20
    material_id = data["id"]

    # Test update
    update_res = client.patch(
        f"/api/v1/materials/{material_id}",
        json={"title": "Updated Hash Tables Guide"},
    )
    assert update_res.status_code == 200
    assert update_res.json()["title"] == "Updated Hash Tables Guide"

    # Test export markdown
    export_res = client.post(
        f"/api/v1/materials/{material_id}/export",
        json={"format": "markdown"},
    )
    assert export_res.status_code == 200
    exp_data = export_res.json()
    assert exp_data["format"] == "markdown"
    assert exp_data["filename"].endswith(".md")
    assert len(exp_data["content"]) > 10

    # Test export HTML
    export_html = client.post(
        f"/api/v1/materials/{material_id}/export",
        json={"format": "html"},
    )
    assert export_html.status_code == 200
    assert "<!DOCTYPE html>" in export_html.json()["content"]


def test_generate_flashcards(client: TestClient):
    payload = {
        "topic": "Big-O Notation Complexity",
        "material_type": "flashcards",
        "student_level": "undergraduate",
        "difficulty": "intermediate",
        "source_mode": "general",
    }
    response = client.post("/api/v1/materials/generate", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["material_type"] == "flashcards"
    assert "content" in data
