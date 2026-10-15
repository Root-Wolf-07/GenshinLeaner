"""Automated tests for Dashboard, Progress, and Recommendations.
"""

from fastapi.testclient import TestClient


def test_dashboard_empty_state_for_new_user(client: TestClient):
    response = client.get("/api/v1/dashboard")
    assert response.status_code == 200
    data = response.json()
    assert data["student_name"] == "Jordan Lee"
    assert data["total_documents"] == 0
    assert data["total_study_materials"] == 0
    assert data["total_quizzes_taken"] == 0
    assert data["average_quiz_score"] == 0.0
    assert data["recent_conversations"] == []
    assert data["recent_documents"] == []
    assert data["recent_materials"] == []
    assert data["recent_quizzes"] == []
    assert len(data["recommended_actions"]) > 0


def test_progress_analytics(client: TestClient):
    response = client.get("/api/v1/progress")
    assert response.status_code == 200
    data = response.json()
    assert "overall_accuracy" in data
    assert "topic_breakdown" in data
    assert "weakest_topics" in data


def test_recommendations_endpoint(client: TestClient):
    response = client.get("/api/v1/recommendations")
    assert response.status_code == 200
    data = response.json()
    assert "recommendations" in data
    assert len(data["recommendations"]) > 0
    rec = data["recommendations"][0]
    assert "action_type" in rec
    assert "reasoning" in rec
