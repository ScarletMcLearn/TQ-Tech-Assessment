import json
from datetime import datetime

import pytest
from app.config import Settings
from app.services.email_reader import MockEmailReader, get_email_reader


def test_mock_email_reader_parses_and_sorts_by_received_at(tmp_path) -> None:
    email_file = tmp_path / "emails.json"
    email_file.write_text(
        json.dumps(
            [
                {
                    "id": "later",
                    "sender": "later@example.com",
                    "subject": "Later",
                    "body": "Second email.",
                    "received_at": "2026-06-04T09:30:00Z",
                },
                {
                    "id": "earlier",
                    "sender": "earlier@example.com",
                    "subject": "Earlier",
                    "body": "First email.",
                    "received_at": "2026-06-04T08:15:00Z",
                },
            ]
        ),
        encoding="utf-8",
    )

    emails = MockEmailReader(email_file).read_emails()

    assert [email.email_id for email in emails] == ["earlier", "later"]
    assert emails[0].sender == "earlier@example.com"
    assert emails[0].received_at == datetime(2026, 6, 4, 8, 15)
    assert emails[0].received_at.tzinfo is None


def test_mock_email_reader_raises_for_missing_file(tmp_path) -> None:
    missing_file = tmp_path / "missing.json"

    with pytest.raises(FileNotFoundError, match="Mock email file not found"):
        MockEmailReader(missing_file).read_emails()


def test_get_email_reader_rejects_unsupported_source() -> None:
    settings = Settings(EMAIL_SOURCE="imap")

    with pytest.raises(ValueError, match="Unsupported EMAIL_SOURCE 'imap'"):
        get_email_reader(settings)
