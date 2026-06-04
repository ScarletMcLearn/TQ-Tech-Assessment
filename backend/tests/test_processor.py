from datetime import datetime

from app.database import Base
from app.models import Notification, ProcessedEmail
from app.services.classifier import RuleBasedClassifier
from app.services.email_reader import EmailMessage
from app.services.processor import EmailProcessor
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


class StaticReader:
    def __init__(self, emails: list[EmailMessage]) -> None:
        self._emails = emails

    def read_emails(self) -> list[EmailMessage]:
        return self._emails


def test_processor_marks_all_emails_and_prevents_duplicate_notifications() -> None:
    engine = create_engine(
        "sqlite:///:memory:", connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    db = TestingSession()

    emails = [
        EmailMessage(
            email_id="important-1",
            sender="ops@example.com",
            subject="Server down",
            body="The production service is down.",
            received_at=datetime(2026, 6, 4, 9, 0, 0),
        ),
        EmailMessage(
            email_id="spam-1",
            sender="promo@example.com",
            subject="Weekly newsletter",
            body="Sponsored promotional newsletter.",
            received_at=datetime(2026, 6, 4, 9, 5, 0),
        ),
    ]

    processor = EmailProcessor(
        db=db, reader=StaticReader(emails), classifier=RuleBasedClassifier()
    )
    first = processor.run_once()
    second = processor.run_once()

    assert first.fetched == 2
    assert first.classified == 2
    assert first.notifications_created == 1
    assert first.ignored == 1
    assert second.fetched == 2
    assert second.skipped_duplicates == 2
    assert second.notifications_created == 0
    assert db.query(Notification).count() == 1
    assert db.query(ProcessedEmail).count() == 2

    db.close()


def test_processor_handles_duplicate_ids_from_same_batch() -> None:
    engine = create_engine(
        "sqlite:///:memory:", connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    db = TestingSession()

    emails = [
        EmailMessage(
            email_id="incident-1",
            sender="ops@example.com",
            subject="Server down",
            body="The production service is down.",
            received_at=datetime(2026, 6, 4, 9, 0, 0),
        ),
        EmailMessage(
            email_id="incident-1",
            sender="ops@example.com",
            subject="Server down",
            body="The production service is down.",
            received_at=datetime(2026, 6, 4, 9, 1, 0),
        ),
    ]

    processor = EmailProcessor(
        db=db, reader=StaticReader(emails), classifier=RuleBasedClassifier()
    )
    result = processor.run_once()

    assert result.fetched == 2
    assert result.classified == 1
    assert result.skipped_duplicates == 1
    assert result.notifications_created == 1
    assert db.query(Notification).count() == 1
    assert db.query(ProcessedEmail).count() == 1

    db.close()


def test_processor_marks_unimportant_emails_as_processed() -> None:
    engine = create_engine(
        "sqlite:///:memory:", connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    db = TestingSession()

    emails = [
        EmailMessage(
            email_id="newsletter-1",
            sender="promo@example.com",
            subject="Weekly newsletter",
            body="Sponsored promotional newsletter.",
            received_at=datetime(2026, 6, 4, 9, 0, 0),
        )
    ]

    processor = EmailProcessor(
        db=db, reader=StaticReader(emails), classifier=RuleBasedClassifier()
    )
    result = processor.run_once()

    assert result.fetched == 1
    assert result.classified == 1
    assert result.notifications_created == 0
    assert result.ignored == 1
    assert db.query(Notification).count() == 0
    assert db.query(ProcessedEmail).count() == 1

    db.close()
