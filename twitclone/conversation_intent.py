"""Conversation-intent options for Ripple's intentional conversation model."""

from __future__ import annotations

CONVERSATION_INTENTS = {
    "open": {
        "label": "Open conversation",
        "short": "All respectful perspectives are welcome.",
    },
    "question": {
        "label": "Looking for answers",
        "short": "Help answer the question or add useful context.",
    },
    "advice": {
        "label": "Advice wanted",
        "short": "Offer practical suggestions or relevant experience.",
    },
    "support": {
        "label": "Support wanted",
        "short": "Respond with empathy and encouragement rather than debate.",
    },
    "debate": {
        "label": "Respectful debate welcome",
        "short": "Disagreement is welcome; keep it constructive and evidence-focused.",
    },
    "sharing": {
        "label": "Just sharing",
        "short": "No advice or debate is being requested.",
    },
}

DEFAULT_CONVERSATION_INTENT = "open"


def normalize_conversation_intent(value: str | None) -> str:
    normalized = (value or DEFAULT_CONVERSATION_INTENT).strip().lower()
    return normalized if normalized in CONVERSATION_INTENTS else DEFAULT_CONVERSATION_INTENT


def conversation_intent_metadata(value: str | None) -> dict[str, str]:
    key = normalize_conversation_intent(value)
    return {"key": key, **CONVERSATION_INTENTS[key]}


__all__ = [
    "CONVERSATION_INTENTS",
    "DEFAULT_CONVERSATION_INTENT",
    "conversation_intent_metadata",
    "normalize_conversation_intent",
]
