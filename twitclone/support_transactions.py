"""Provider-neutral creator support transaction contract for Sprint 15.

This module defines vocabulary and validation only. It intentionally performs no
checkout, payment-provider API calls, persistence, payout, or entitlement grant.
"""

from dataclasses import dataclass
from enum import StrEnum

SUPPORTED_CURRENCIES = {"USD"}
MIN_SUPPORT_AMOUNT_CENTS = 100
MAX_SUPPORT_AMOUNT_CENTS = 100_000


class SupportTransactionStatus(StrEnum):
    CREATED = "created"
    PENDING = "pending"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELED = "canceled"
    PARTIALLY_REFUNDED = "partially_refunded"
    REFUNDED = "refunded"
    CHARGEBACK = "chargeback"


class SupportPayoutStatus(StrEnum):
    NOT_READY = "not_ready"
    PENDING = "pending"
    PAID = "paid"
    FAILED = "failed"
    REVERSED = "reversed"


TRANSACTION_TRANSITIONS = {
    SupportTransactionStatus.CREATED: {
        SupportTransactionStatus.PENDING,
        SupportTransactionStatus.CANCELED,
        SupportTransactionStatus.FAILED,
    },
    SupportTransactionStatus.PENDING: {
        SupportTransactionStatus.SUCCEEDED,
        SupportTransactionStatus.CANCELED,
        SupportTransactionStatus.FAILED,
    },
    SupportTransactionStatus.SUCCEEDED: {
        SupportTransactionStatus.PARTIALLY_REFUNDED,
        SupportTransactionStatus.REFUNDED,
        SupportTransactionStatus.CHARGEBACK,
    },
    SupportTransactionStatus.PARTIALLY_REFUNDED: {
        SupportTransactionStatus.PARTIALLY_REFUNDED,
        SupportTransactionStatus.REFUNDED,
        SupportTransactionStatus.CHARGEBACK,
    },
    SupportTransactionStatus.REFUNDED: {SupportTransactionStatus.CHARGEBACK},
    SupportTransactionStatus.FAILED: set(),
    SupportTransactionStatus.CANCELED: set(),
    SupportTransactionStatus.CHARGEBACK: set(),
}

PAYOUT_TRANSITIONS = {
    SupportPayoutStatus.NOT_READY: {SupportPayoutStatus.PENDING},
    SupportPayoutStatus.PENDING: {SupportPayoutStatus.PAID, SupportPayoutStatus.FAILED},
    SupportPayoutStatus.PAID: {SupportPayoutStatus.REVERSED},
    SupportPayoutStatus.FAILED: {SupportPayoutStatus.PENDING},
    SupportPayoutStatus.REVERSED: set(),
}


@dataclass(frozen=True)
class SupportFeeBreakdown:
    """Auditable fee allocation for one support transaction."""

    gross_amount_cents: int
    platform_fee_cents: int
    provider_fee_cents: int
    creator_net_cents: int
    currency: str = "USD"

    def validate(self):
        currency = self.currency.upper()
        if currency not in SUPPORTED_CURRENCIES:
            raise ValueError("Unsupported support currency.")
        if not MIN_SUPPORT_AMOUNT_CENTS <= self.gross_amount_cents <= MAX_SUPPORT_AMOUNT_CENTS:
            raise ValueError("Support amount is outside the allowed range.")
        values = (
            self.platform_fee_cents,
            self.provider_fee_cents,
            self.creator_net_cents,
        )
        if any(value < 0 for value in values):
            raise ValueError("Support fee components cannot be negative.")
        if sum(values) != self.gross_amount_cents:
            raise ValueError("Support fee components must reconcile to the gross amount.")
        return self


@dataclass(frozen=True)
class SupportReceiptContract:
    """Minimum receipt fields Ripple must be able to present after settlement."""

    transaction_reference: str
    creator_user_id: int
    gross_amount_cents: int
    currency: str
    platform_fee_cents: int
    provider_fee_cents: int
    creator_net_cents: int
    status: SupportTransactionStatus

    def validate(self):
        if not self.transaction_reference.strip():
            raise ValueError("A transaction reference is required.")
        if self.creator_user_id < 1:
            raise ValueError("A creator user ID is required.")
        SupportFeeBreakdown(
            gross_amount_cents=self.gross_amount_cents,
            platform_fee_cents=self.platform_fee_cents,
            provider_fee_cents=self.provider_fee_cents,
            creator_net_cents=self.creator_net_cents,
            currency=self.currency,
        ).validate()
        return self


def can_transition_transaction(current, target):
    current_status = SupportTransactionStatus(current)
    target_status = SupportTransactionStatus(target)
    return target_status in TRANSACTION_TRANSITIONS[current_status]


def can_transition_payout(current, target):
    current_status = SupportPayoutStatus(current)
    target_status = SupportPayoutStatus(target)
    return target_status in PAYOUT_TRANSITIONS[current_status]


__all__ = [
    "MAX_SUPPORT_AMOUNT_CENTS",
    "MIN_SUPPORT_AMOUNT_CENTS",
    "PAYOUT_TRANSITIONS",
    "SUPPORTED_CURRENCIES",
    "SupportFeeBreakdown",
    "SupportPayoutStatus",
    "SupportReceiptContract",
    "SupportTransactionStatus",
    "TRANSACTION_TRANSITIONS",
    "can_transition_payout",
    "can_transition_transaction",
]
