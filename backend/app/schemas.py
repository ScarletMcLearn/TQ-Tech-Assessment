from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict


class Priority(StrEnum):
    high = "HIGH"
    medium = "MEDIUM"
    low = "LOW"


class Category(StrEnum):
    payment_issue = "PAYMENT_ISSUE"
    server_down = "SERVER_DOWN"
    client_complaint = "CLIENT_COMPLAINT"
    urgent_request = "URGENT_REQUEST"
    subscription = "SUBSCRIPTION"
    spam = "SPAM"
    other = "OTHER"


class ClassificationDecision(BaseModel):
    important: bool
    priority: Priority
    category: Category
    reason: str


class NotificationOut(BaseModel):
    id: int
    email_id: str
    sender: str
    subject: str
    priority: Priority
    category: Category
    reason: str
    received_at: datetime
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProcessedEmailOut(BaseModel):
    id: int
    email_id: str
    processed_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProcessingSummary(BaseModel):
    fetched: int = 0
    skipped_duplicates: int = 0
    classified: int = 0
    notifications_created: int = 0
    ignored: int = 0


class RunOnceResponse(BaseModel):
    source: str
    summary: ProcessingSummary


class HealthResponse(BaseModel):
    status: str
    database: str
    email_source: str
    ai_provider: str
    scheduler: dict[str, int | bool]
