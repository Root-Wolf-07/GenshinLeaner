"""Pytest fixtures and test database setup.
"""

from typing import Generator
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from backend.db.base import Base
from backend.db.session import get_db
from backend.dependencies import get_current_user, hash_password
from backend.main import app
from backend.models.user import User

# In-memory SQLite database for isolated test runs
TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    """Create all tables in memory once for test session."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    """Provide a transactional database session rolled back after each test."""
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def test_user(db_session: Session) -> User:
    """Create a persistent test user for authenticated requests."""
    user = User(
        id="test-user-uuid-12345",
        student_id="STU-TEST1234",
        email="student@testing.edu",
        normalized_email="student@testing.edu",
        username="test_student",
        hashed_password=hash_password("ValidPassword123!"),
        full_name="Jordan Lee",
        student_level="undergraduate",
        is_verified=True,
        session_version=1,
        preferences={"theme": "dark", "katex_enabled": True},
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def other_user(db_session: Session) -> User:
    """Create a second distinct user to verify ownership isolation."""
    user = User(
        id="other-user-uuid-67890",
        student_id="STU-OTHER567",
        email="other@testing.edu",
        normalized_email="other@testing.edu",
        username="other_student",
        hashed_password=hash_password("OtherPassword123!"),
        full_name="Sam Smith",
        student_level="graduate",
        is_verified=True,
        session_version=1,
        preferences={},
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def client(db_session: Session, test_user: User) -> Generator[TestClient, None, None]:
    """Test client with database and current_user dependencies overridden."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    def override_get_current_user():
        return test_user

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
