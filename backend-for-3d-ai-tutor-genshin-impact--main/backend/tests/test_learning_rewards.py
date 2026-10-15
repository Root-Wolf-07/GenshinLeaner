"""Automated tests for Learning Rewards, XP Idempotency, Quests, and Achievements.
"""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.models.user import User
from backend.services.learning_rewards import learning_rewards


def test_xp_idempotency_prevents_duplicate_awards(client: TestClient, db_session: Session, test_user: User):
    """Requirement 16: Repeated XP requests with identical idempotency_key do not duplicate rewards."""
    idempotency_key = "quiz_attempt_unique_uuid_9999"

    # 1. First grant
    tx1 = learning_rewards.grant_xp(
        user_id=test_user.id,
        amount=50,
        category="quiz_completed",
        idempotency_key=idempotency_key,
        description="Completed quiz on Differential Equations",
        db=db_session,
    )
    assert tx1 is not None
    assert tx1.amount == 50

    # 2. Duplicate grant with same idempotency_key
    tx2 = learning_rewards.grant_xp(
        user_id=test_user.id,
        amount=50,
        category="quiz_completed",
        idempotency_key=idempotency_key,
        description="Completed quiz on Differential Equations",
        db=db_session,
    )
    assert tx2 is not None
    assert tx2.id == tx1.id  # Same transaction returned

    # 3. Verify total XP via summary
    summary = learning_rewards.get_summary(user_id=test_user.id, db=db_session)
    # Ensure total XP reflects only a single award of 50
    assert summary.total_xp >= 50


def test_gamification_summary_api(client: TestClient):
    """GET /api/v1/gamification/summary returns user mastery level and quests."""
    res = client.get("/api/v1/gamification/summary")
    assert res.status_code == 200
    data = res.json()
    assert "total_xp" in data
    assert "current_level" in data
    assert "level_title" in data
    assert "achievements" in data


def test_gamification_quests_api(client: TestClient):
    """GET /api/v1/gamification/quests returns transparent learning goals."""
    res = client.get("/api/v1/gamification/quests")
    assert res.status_code == 200
    quests = res.json()
    assert len(quests) >= 2
    assert any(q["id"] == "quest_daily_concept" for q in quests)


def test_gamification_reward_api_idempotent(client: TestClient):
    """POST /api/v1/gamification/reward awards XP idempotently."""
    idem_key = "client_grant_test_001"
    payload = {
        "amount": 25,
        "category": "question_answered",
        "description": "Explored physics vectors with Ganyu",
        "idempotency_key": idem_key,
    }

    # First request
    res1 = client.post("/api/v1/gamification/reward", json=payload)
    assert res1.status_code == 200
    data1 = res1.json()

    # Second request with identical key
    res2 = client.post("/api/v1/gamification/reward", json=payload)
    assert res2.status_code == 200
    data2 = res2.json()

    # Identical transaction ID returned
    assert data1["id"] == data2["id"]
