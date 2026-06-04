from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import Notification, ProcessedEmail
from app.schemas import ProcessingSummary
from app.services.classifier import OpenAIClassifier, RuleBasedClassifier
from app.services.email_reader import EmailReader


class EmailProcessor:
    def __init__(
        self,
        db: Session,
        reader: EmailReader,
        classifier: RuleBasedClassifier | OpenAIClassifier,
    ) -> None:
        self._db = db
        self._reader = reader
        self._classifier = classifier

    def run_once(self) -> ProcessingSummary:
        summary = ProcessingSummary()

        for email in self._reader.read_emails():
            summary.fetched += 1
            if self._already_processed(email.email_id):
                summary.skipped_duplicates += 1
                continue

            decision = self._classifier.classify(email)
            summary.classified += 1

            if decision.important:
                self._db.add(
                    Notification(
                        email_id=email.email_id,
                        sender=email.sender,
                        subject=email.subject,
                        priority=decision.priority.value,
                        category=decision.category.value,
                        reason=decision.reason,
                        received_at=email.received_at,
                    )
                )
                summary.notifications_created += 1
            else:
                summary.ignored += 1

            self._db.add(ProcessedEmail(email_id=email.email_id))

            try:
                self._db.commit()
            except IntegrityError:
                self._db.rollback()
                summary.skipped_duplicates += 1
                if decision.important and summary.notifications_created > 0:
                    summary.notifications_created -= 1

        return summary

    def _already_processed(self, email_id: str) -> bool:
        return (
            self._db.query(ProcessedEmail)
            .filter(ProcessedEmail.email_id == email_id)
            .first()
            is not None
        )
