from fastapi import APIRouter, Depends
from sqlalchemy import case, text
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.database import get_db
from app.models import Notification, ProcessedEmail
from app.schemas import (
    HealthResponse,
    NotificationOut,
    ProcessedEmailOut,
    RunOnceResponse,
)
from app.services.classifier import get_classifier
from app.services.email_reader import get_email_reader
from app.services.processor import EmailProcessor

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health(
    db: Session = Depends(get_db), settings: Settings = Depends(get_settings)
) -> dict:
    db.execute(text("SELECT 1"))
    return {
        "status": "ok",
        "database": "ok",
        "email_source": settings.email_source,
        "ai_provider": settings.ai_provider,
        "scheduler": {
            "enabled": True,
            "poll_interval_seconds": settings.poll_interval_seconds,
        },
    }


@router.get("/notifications", response_model=list[NotificationOut])
def list_notifications(db: Session = Depends(get_db)) -> list[Notification]:
    priority_order = case(
        (Notification.priority == "HIGH", 0),
        (Notification.priority == "MEDIUM", 1),
        (Notification.priority == "LOW", 2),
        else_=3,
    )
    return (
        db.query(Notification)
        .order_by(
            priority_order, Notification.received_at.desc(), Notification.id.desc()
        )
        .all()
    )


@router.post("/agent/run-once", response_model=RunOnceResponse)
def run_agent_once(
    db: Session = Depends(get_db), settings: Settings = Depends(get_settings)
) -> dict:
    processor = EmailProcessor(
        db=db,
        reader=get_email_reader(settings),
        classifier=get_classifier(settings),
    )
    summary = processor.run_once()
    return {"source": settings.email_source, "summary": summary}


@router.get("/debug/processed", response_model=list[ProcessedEmailOut])
def list_processed(db: Session = Depends(get_db)) -> list[ProcessedEmail]:
    return db.query(ProcessedEmail).order_by(ProcessedEmail.processed_at.desc()).all()
