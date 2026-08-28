"""Derived reviewer-quality metrics for Ripple community context.

Reputation is intentionally computed from resolved review history rather than
stored as a mutable score. This keeps the metric auditable and prevents stale
or manually-adjusted reputation values from influencing community review.
"""

from dataclasses import dataclass

from twitclone.fact_context_models import FactContextAssessment


@dataclass(frozen=True)
class ReviewerReputation:
    total_assessments: int
    resolved_assessments: int
    aligned_assessments: int
    agreement_rate: int | None
    level: str
    label: str
    description: str


def _level_for(resolved_assessments: int, agreement_rate: int | None):
    if resolved_assessments < 3 or agreement_rate is None:
        return (
            "new",
            "New reviewer",
            "Building a review history. Reputation does not change vote weight.",
        )
    if resolved_assessments >= 20 and agreement_rate >= 80:
        return (
            "strong",
            "Strong review record",
            "A substantial resolved review history with high agreement to final outcomes.",
        )
    if resolved_assessments >= 8 and agreement_rate >= 70:
        return (
            "established",
            "Established reviewer",
            "A meaningful resolved review history with consistent outcome agreement.",
        )
    return (
        "developing",
        "Developing reviewer",
        "Has resolved review history; continued evidence-based participation will refine the record.",
    )


def reviewer_reputation(user_id: int) -> ReviewerReputation:
    assessments = FactContextAssessment.query.filter_by(reviewer_id=user_id).all()
    resolved = [
        item
        for item in assessments
        if item.submission.status == "approved" and item.submission.outcome is not None
    ]
    aligned = [item for item in resolved if item.assessment == item.submission.outcome]
    agreement_rate = round(len(aligned) * 100 / len(resolved)) if resolved else None
    level, label, description = _level_for(len(resolved), agreement_rate)
    return ReviewerReputation(
        total_assessments=len(assessments),
        resolved_assessments=len(resolved),
        aligned_assessments=len(aligned),
        agreement_rate=agreement_rate,
        level=level,
        label=label,
        description=description,
    )


__all__ = ["ReviewerReputation", "reviewer_reputation"]
