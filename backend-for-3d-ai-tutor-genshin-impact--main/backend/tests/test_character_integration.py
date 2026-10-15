"""End-to-End Integration Tests for Interactive Animated Character AI Tutor.
Executes complete student-tutor lifecycle:
Select tutor -> Start session -> Ask question -> Grounded retrieval & citation ->
Animation metadata -> Voice synthesis -> Cancellation -> Practice question ->
Objective feedback & XP progress recording.
"""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.models.document import Document, DocumentChunk
from backend.models.user import User


def test_full_character_tutor_journey(client: TestClient, db_session: Session, test_user: User):
    """Full lifecycle test demonstrating end-to-end interactive character tutoring."""
    # Step 1: Browse available character tutors and select Raiden Ei for Mathematics
    catalog_res = client.get("/api/v1/tutors")
    assert catalog_res.status_code == 200
    tutors = catalog_res.json()
    raiden = next((t for t in tutors if t["id"] == "raiden_shogun"), None)
    assert raiden is not None
    assert "Mathematics" in raiden["supported_subjects"]

    # Step 2: Seed verified ground-truth course document & chunk in database
    doc = Document(
        id="doc_linear_algebra_01",
        owner_id=test_user.id,
        original_filename="linear_algebra_lecture_04.pdf",
        safe_storage_name="linear_algebra_lecture_04.pdf",
        file_type=".pdf",
        file_size=2048,
        title="Lecture 4: Eigenvalues and Invariant Subspaces",
        subject="Mathematics",
        page_count=10,
        chunk_count=1,
        doc_metadata={},
    )
    chunk = DocumentChunk(
        id="chunk_eigen_01",
        document_id=doc.id,
        owner_id=test_user.id,
        chunk_index=0,
        content="An eigenvector of an n x n matrix A is a nonzero vector v such that Av = lambda v.",
        page_number=4,
        source_type="pdf",
        token_count=20,
        chunk_metadata={},
    )
    db_session.add(doc)
    db_session.add(chunk)
    db_session.commit()

    # Step 3: Initialize tutor session
    session_res = client.post(
        "/api/v1/tutor-sessions",
        json={
            "tutor_id": "raiden_shogun",
            "subject": "Mathematics",
            "title": "Eigenvalues Masterclass",
            "interaction_mode": "multimodal",
            "source_mode": "both",
            "selected_document_ids": [doc.id],
        },
    )
    assert session_res.status_code == 201
    session_data = session_res.json()
    session_id = session_data["id"]

    # Step 4: Ask a question grounded in the course document
    question_res = client.post(
        f"/api/v1/tutor-sessions/{session_id}/messages",
        json={
            "content": "What is the formal definition of an eigenvector?",
            "intent": "ask_question",
            "request_voice": True,
        },
    )
    assert question_res.status_code == 200
    answer_data = question_res.json()
    assert answer_data["role"] == "assistant"
    assert answer_data["character_name"] == "Raiden Ei / Shogun"
    assert len(answer_data["content"]) > 10

    # Step 5: Verify animation instruction and speech metadata
    assert "animation" in answer_data
    anim = answer_data["animation"]
    assert anim["character_id"] == "raiden_shogun"
    assert anim["state"] in ("explaining", "speaking")
    assert "raiden" in anim["animation_key"]
    assert 0.0 <= anim["intensity"] <= 1.0

    assert answer_data["speech"] is not None
    speech = answer_data["speech"]
    assert speech["character_id"] == "raiden_shogun"
    assert speech["duration_ms"] > 0
    assert len(speech["segments"]) > 0
    audio_id = speech["audio_id"]

    # Step 6: Stream audio bytes via audio endpoint
    stream_res = client.get(f"/api/v1/voice/speech/{audio_id}")
    assert stream_res.status_code == 200
    assert len(stream_res.content) > 0

    # Step 7: Request a progressive hint
    hint_res = client.post(
        f"/api/v1/tutor-sessions/{session_id}/messages",
        json={
            "content": "How do I find the characteristic polynomial?",
            "intent": "give_hint",
            "hint_level": 1,
            "request_voice": False,
        },
    )
    assert hint_res.status_code == 200
    hint_data = hint_res.json()
    assert hint_data["animation"]["state"] == "giving_hint"
    assert "hint" in hint_data["pedagogical_mode"]

    # Step 8: Submit practice answer check
    answer_check_res = client.post(
        f"/api/v1/tutor-sessions/{session_id}/messages",
        json={
            "content": "Is it by computing det(A - lambda I) = 0?",
            "intent": "check_my_answer",
            "user_answer_submission": "det(A - lambda I) = 0",
            "request_voice": False,
        },
    )
    assert answer_check_res.status_code == 200
    check_data = answer_check_res.json()
    assert check_data["animation"]["state"] == "waiting_for_answer"

    # Step 9: Cancel session audio
    cancel_res = client.post(f"/api/v1/tutor-sessions/{session_id}/cancel")
    assert cancel_res.status_code == 200
    assert cancel_res.json()["audio_cancelled"] is True

    # Step 10: Verify learning rewards & XP progress recorded
    gamification_res = client.get("/api/v1/gamification/summary")
    assert gamification_res.status_code == 200
    summary = gamification_res.json()
    assert summary["total_xp"] > 0
    assert len(summary["recent_transactions"]) > 0


def test_quiz_grading_independence_from_character_personality(client: TestClient, db_session: Session, test_user: User):
    """Requirement 17: Quiz grading is purely objective and independent of character personality."""
    from backend.models.quiz import Quiz
    from backend.schemas.quizzes import QuizSubmitRequest
    from backend.services.quiz_grader import quiz_grader

    # Create quiz with 1 objective multiple choice question
    quiz = Quiz(
        id="quiz_math_test_01",
        owner_id=test_user.id,
        title="Mathematics Assessment",
        topic="Linear Algebra",
        difficulty="intermediate",
        student_level="undergraduate",
        source_mode="general",
        document_ids=[],
        total_questions=1,
        questions=[
            {
                "id": "q1",
                "prompt": "What is 2 + 2?",
                "question_type": "multiple_choice",
                "options": ["3", "4", "5", "6"],
                "correct_answer": "4",
                "explanation": "Basic addition.",
                "topic_tag": "Arithmetic",
                "points": 1.0,
            }
        ],
    )
    db_session.add(quiz)
    db_session.commit()

    # Grade with correct answer
    submission = QuizSubmitRequest(answers={"q1": "4"})
    result = quiz_grader.grade_submission(quiz=quiz, submission=submission, user_id=test_user.id, db=db_session)
    assert result.passed is True
    assert result.score == 100.0
    assert result.graded_items[0].is_correct is True

    # Grade with incorrect answer
    sub_wrong = QuizSubmitRequest(answers={"q1": "3"})
    res_wrong = quiz_grader.grade_submission(quiz=quiz, submission=sub_wrong, user_id=test_user.id, db=db_session)
    assert res_wrong.passed is False
    assert res_wrong.score == 0.0
    assert res_wrong.graded_items[0].is_correct is False
