from datetime import datetime

from app.schemas import Category, Priority
from app.services.classifier import OpenAIClassifier, RuleBasedClassifier
from app.services.email_reader import EmailMessage


def make_email(subject: str, body: str) -> EmailMessage:
    return EmailMessage(
        email_id=subject.lower().replace(" ", "-"),
        sender="sender@example.com",
        subject=subject,
        body=body,
        received_at=datetime(2026, 6, 4, 9, 0, 0),
    )


def test_payment_failure_is_high_priority_payment_issue() -> None:
    result = RuleBasedClassifier().classify(
        make_email("Payment failure", "The customer card declined on the invoice.")
    )

    assert result.important is True
    assert result.priority == Priority.high
    assert result.category == Category.payment_issue


def test_server_down_is_high_priority_server_down() -> None:
    result = RuleBasedClassifier().classify(
        make_email("Server down", "Production API unavailable for all users.")
    )

    assert result.important is True
    assert result.priority == Priority.high
    assert result.category == Category.server_down


def test_client_complaint_is_high_priority() -> None:
    result = RuleBasedClassifier().classify(
        make_email(
            "Client complaint", "This is a formal complaint from an unhappy customer."
        )
    )

    assert result.important is True
    assert result.priority == Priority.high
    assert result.category == Category.client_complaint


def test_subscription_notice_is_low_priority_but_important() -> None:
    result = RuleBasedClassifier().classify(
        make_email(
            "Subscription renewal notice", "Your plan renewal is scheduled soon."
        )
    )

    assert result.important is True
    assert result.priority == Priority.low
    assert result.category == Category.subscription


def test_newsletter_is_not_important() -> None:
    result = RuleBasedClassifier().classify(
        make_email("Weekly newsletter", "Read our sponsored industry newsletter.")
    )

    assert result.important is False
    assert result.category == Category.spam


def test_refund_request_is_medium_priority_urgent_request() -> None:
    result = RuleBasedClassifier().classify(
        make_email("Refund request", "Please refund the customer as soon as possible.")
    )

    assert result.important is True
    assert result.priority == Priority.medium
    assert result.category == Category.urgent_request


def test_unknown_email_is_not_important_other() -> None:
    result = RuleBasedClassifier().classify(
        make_email("Team lunch", "The team lunch menu is ready for Friday.")
    )

    assert result.important is False
    assert result.priority == Priority.low
    assert result.category == Category.other


def test_openai_classifier_falls_back_to_rules_when_provider_fails() -> None:
    classifier = OpenAIClassifier(api_key="bad-key", fallback=RuleBasedClassifier())
    result = classifier.classify(
        make_email("Server down", "The production API is unavailable.")
    )

    assert result.important is True
    assert result.priority == Priority.high
    assert result.category == Category.server_down
