import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Protocol

from app.config import Settings


@dataclass(frozen=True)
class EmailMessage:
    email_id: str
    sender: str
    subject: str
    body: str
    received_at: datetime


class EmailReader(Protocol):
    def read_emails(self) -> list[EmailMessage]: ...


class MockEmailReader:
    def __init__(self, path: Path) -> None:
        self._path = path

    def read_emails(self) -> list[EmailMessage]:
        if not self._path.exists():
            raise FileNotFoundError(f"Mock email file not found: {self._path}")

        raw = json.loads(self._path.read_text(encoding="utf-8"))
        emails = [self._parse_email(item) for item in raw]
        return sorted(emails, key=lambda email: email.received_at)

    @staticmethod
    def _parse_email(item: dict) -> EmailMessage:
        return EmailMessage(
            email_id=str(item["id"]),
            sender=str(item["sender"]),
            subject=str(item["subject"]),
            body=str(item["body"]),
            received_at=_parse_datetime(str(item["received_at"])),
        )


def _parse_datetime(value: str) -> datetime:
    normalized = value.replace("Z", "+00:00")
    parsed = datetime.fromisoformat(normalized)
    return parsed.replace(tzinfo=None)


def get_email_reader(settings: Settings) -> EmailReader:
    source = settings.email_source.lower()
    if source != "mock":
        raise ValueError(
            f"Unsupported EMAIL_SOURCE '{settings.email_source}'. Use 'mock'."
        )
    return MockEmailReader(settings.mock_email_path)
