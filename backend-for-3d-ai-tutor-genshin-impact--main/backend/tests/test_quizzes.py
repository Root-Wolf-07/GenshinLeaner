"""Automated tests for Quiz generation, answer security, grading, and attempts.
"""

from fastapi.testclient import TestClient


def test_quiz_generation_and_answer_hiding(client: TestClient):
    payload = {
        "topic": "Recursion and Call Stacks",
        "question_count": 3,
        "difficulty": "intermediate",
        "student_level": "undergraduate",
        "source_mode": "general",
    }
    response = client.post("/api/v1/quizzes/generate", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["topic"] == "Recursion and Call Stacks"
    assert len(data["questions"]) > 0

    quiz_id = data["id"]

    # CRITICAL SECURITY CHECK: Ensure correct answers are NOT in the questions payload
    for q in data["questions"]:
        assert "correct_answer" not in q
        assert "explanation" not in q

    # Retrieve quiz via GET and verify answers remain hidden
    get_res = client.get(f"/api/v1/quizzes/{quiz_id}")
    assert get_res.status_code == 200
    for q in get_res.json()["questions"]:
        assert "correct_answer" not in q
        assert "explanation" not in q


def test_quiz_submission_and_backend_grading(client: TestClient):
    # 1. Generate quiz
    gen_res = client.post(
        "/api/v1/quizzes/generate",
        json={"topic": "Sorting Algorithms", "question_count": 2, "source_mode": "general"},
    )
    quiz_id = gen_res.json()["id"]
    questions = gen_res.json()["questions"]
    q1_id = questions[0]["id"]
    q2_id = questions[1]["id"]

    # 2. Submit answers
    submit_payload = {
        "answers": {
            q1_id: "Empirical verification and invariant checking",  # typically correct in fallback
            q2_id: "False",  # incorrect
        }
    }
    sub_res = client.post(f"/api/v1/quizzes/{quiz_id}/submit", json=submit_payload)
    assert sub_res.status_code == 200
    result = sub_res.json()

    assert "score" in result
    assert "graded_items" in result
    assert len(result["graded_items"]) == 2
    # At feedback stage, correct answers and explanations are legitimately revealed
    assert "correct_answer" in result["graded_items"][0]
    assert "explanation" in result["graded_items"][0]

    # Verify attempt was recorded in attempts history
    attempt_res = client.get(f"/api/v1/quizzes/{quiz_id}/attempts")
    assert attempt_res.status_code == 200
    assert len(attempt_res.json()) >= 1
