from collections.abc import Generator
from datetime import datetime

import pytest
from app.config import Settings, get_settings
from app.database import Base, get_db
from app.main import app
from app.models import Notification, ProcessedEmail
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    db = TestingSession()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def client(db_session: Session) -> Generator[TestClient, None, None]:
    def override_get_db() -> Generator[Session, None, None]:
        yield db_session

    def override_get_settings() -> Settings:
        return Settings(
            EMAIL_SOURCE="mock",
            AI_PROVIDER="rules",
            POLL_INTERVAL_SECONDS=45,
        )

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_settings] = override_get_settings
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()


def add_notification(
    db: Session,
    *,
    email_id: str,
    priority: str,
    received_at: datetime,
) -> None:
    db.add(
        Notification(
            email_id=email_id,
            sender=f"{email_id}@example.com",
            subject=email_id,
            priority=priority,
            category="OTHER",
            reason="Test notification.",
            received_at=received_at,
        )
    )
    db.commit()


def test_health_returns_configured_status(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "database": "ok",
        "email_source": "mock",
        "ai_provider": "rules",
        "scheduler": {
            "enabled": True,
            "poll_interval_seconds": 45,
        },
    }


def test_notifications_are_sorted_by_priority_then_newest_received(
    client: TestClient, db_session: Session
) -> None:
    add_notification(
        db_session,
        email_id="low-new",
        priority="LOW",
        received_at=datetime(2026, 6, 4, 12, 0),
    )
    add_notification(
        db_session,
        email_id="high-old",
        priority="HIGH",
        received_at=datetime(2026, 6, 4, 8, 0),
    )
    add_notification(
        db_session,
        email_id="medium",
        priority="MEDIUM",
        received_at=datetime(2026, 6, 4, 10, 0),
    )
    add_notification(
        db_session,
        email_id="high-new",
        priority="HIGH",
        received_at=datetime(2026, 6, 4, 11, 0),
    )

    response = client.get("/notifications")

    assert response.status_code == 200
    assert [item["email_id"] for item in response.json()] == [
        "high-new",
        "high-old",
        "medium",
        "low-new",
    ]


def test_debug_processed_returns_newest_processed_first(
    client: TestClient, db_session: Session
) -> None:
    db_session.add_all(
        [
            ProcessedEmail(email_id="old", processed_at=datetime(2026, 6, 4, 8, 0)),
            ProcessedEmail(email_id="new", processed_at=datetime(2026, 6, 4, 9, 0)),
        ]
    )
    db_session.commit()

    response = client.get("/debug/processed")

    assert response.status_code == 200
    assert [item["email_id"] for item in response.json()] == ["new", "old"]


def test_run_once_processes_mock_source_and_returns_summary(
    client: TestClient, tmp_path
) -> None:
    email_file = tmp_path / "emails.json"
    email_file.write_text(
        """[
            {
                "id": "incident-1",
                "sender": "ops@example.com",
                "subject": "Server down",
                "body": "Production API unavailable for all users.",
                "received_at": "2026-06-04T09:00:00Z"
            },
            {
                "id": "newsletter-1",
                "sender": "promo@example.com",
                "subject": "Weekly newsletter",
                "body": "Sponsored promotional newsletter.",
                "received_at": "2026-06-04T09:05:00Z"
            }
        ]""",
        encoding="utf-8",
    )

    def override_get_settings() -> Settings:
        return Settings(
            EMAIL_SOURCE="mock",
            MOCK_EMAIL_FILE=str(email_file),
            AI_PROVIDER="rules",
            POLL_INTERVAL_SECONDS=45,
        )

    app.dependency_overrides[get_settings] = override_get_settings

    response = client.post("/agent/run-once")

    assert response.status_code == 200
    assert response.json() == {
        "source": "mock",
        "summary": {
            "fetched": 2,
            "skipped_duplicates": 0,
            "classified": 2,
            "notifications_created": 1,
            "ignored": 1,
        },
    }
