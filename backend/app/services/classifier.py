import json
from dataclasses import dataclass

from app.config import Settings
from app.schemas import Category, ClassificationDecision, Priority
from app.services.email_reader import EmailMessage


@dataclass(frozen=True)
class KeywordRule:
    terms: tuple[str, ...]
    priority: Priority
    category: Category
    reason: str


class RuleBasedClassifier:
    """Deterministic fallback that satisfies the assessment without credentials."""

    def __init__(self) -> None:
        self._rules = (
            KeywordRule(
                terms=(
                    "payment failed",
                    "payment failure",
                    "failed payment",
                    "card declined",
                    "payment was declined",
                    "billing issue",
                    "invoice overdue",
                    "past due",
                    "failed invoice",
                    "charge failed",
                ),
                priority=Priority.high,
                category=Category.payment_issue,
                reason=(
                    "The email describes a payment or billing issue that needs "
                    "attention."
                ),
            ),
            KeywordRule(
                terms=(
                    "server down",
                    "service down",
                    "outage",
                    "production outage",
                    "production issue",
                    "api unavailable",
                    "database unreachable",
                    "critical error",
                    "incident",
                ),
                priority=Priority.high,
                category=Category.server_down,
                reason=(
                    "The email reports a production outage or service "
                    "availability issue."
                ),
            ),
            KeywordRule(
                terms=(
                    "client complaint",
                    "customer complaint",
                    "angry client",
                    "unhappy customer",
                    "escalation",
                    "sla breach",
                    "formal complaint",
                ),
                priority=Priority.high,
                category=Category.client_complaint,
                reason="The email contains a client complaint or escalation.",
            ),
            KeywordRule(
                terms=(
                    "urgent request",
                    "urgent customer request",
                    "needs immediate",
                    "as soon as possible",
                    "refund request",
                    "refund",
                    "chargeback",
                    "cancel my account",
                ),
                priority=Priority.medium,
                category=Category.urgent_request,
                reason=(
                    "The email contains an urgent customer request that should "
                    "be reviewed."
                ),
            ),
            KeywordRule(
                terms=(
                    "subscription renewal",
                    "renewal notice",
                    "plan renewal",
                    "account notice",
                    "automated account",
                    "automated report",
                    "scheduled digest",
                ),
                priority=Priority.low,
                category=Category.subscription,
                reason="The email is a low-priority automated or subscription notice.",
            ),
        )
        self._spam_terms = (
            "newsletter",
            "promotion",
            "promotional",
            "discount",
            "limited time",
            "buy now",
            "free prize",
            "winner",
            "seo services",
            "crypto",
            "sponsored",
        )

    def classify(self, email: EmailMessage) -> ClassificationDecision:
        text = f"{email.subject}\n{email.body}".lower()

        for rule in self._rules:
            if any(term in text for term in rule.terms):
                return ClassificationDecision(
                    important=True,
                    priority=rule.priority,
                    category=rule.category,
                    reason=rule.reason,
                )

        if any(term in text for term in self._spam_terms):
            return ClassificationDecision(
                important=False,
                priority=Priority.low,
                category=Category.spam,
                reason=(
                    "The email appears to be promotional, spam, or a general "
                    "newsletter."
                ),
            )

        return ClassificationDecision(
            important=False,
            priority=Priority.low,
            category=Category.other,
            reason=(
                "The email does not match any important operational or customer "
                "signal."
            ),
        )


class OpenAIClassifier:
    def __init__(self, api_key: str, fallback: RuleBasedClassifier) -> None:
        self._api_key = api_key
        self._fallback = fallback

    def classify(self, email: EmailMessage) -> ClassificationDecision:
        try:
            from openai import OpenAI

            client = OpenAI(api_key=self._api_key)
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                response_format={"type": "json_object"},
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Classify emails for an operations dashboard. "
                            "Return only JSON with important, priority, "
                            "category, and reason. Priority must be HIGH, "
                            "MEDIUM, or LOW. Category must be PAYMENT_ISSUE, "
                            "SERVER_DOWN, CLIENT_COMPLAINT, URGENT_REQUEST, "
                            "SUBSCRIPTION, SPAM, or OTHER."
                        ),
                    },
                    {
                        "role": "user",
                        "content": (
                            f"From: {email.sender}\n"
                            f"Subject: {email.subject}\n\n"
                            f"{email.body}"
                        ),
                    },
                ],
            )
            content = response.choices[0].message.content or "{}"
            return ClassificationDecision.model_validate(json.loads(content))
        except Exception:
            return self._fallback.classify(email)


def get_classifier(settings: Settings) -> RuleBasedClassifier | OpenAIClassifier:
    fallback = RuleBasedClassifier()
    if settings.ai_provider.lower() == "openai" and settings.openai_api_key:
        return OpenAIClassifier(api_key=settings.openai_api_key, fallback=fallback)
    return fallback
