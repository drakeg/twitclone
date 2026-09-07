"""Sprint 15 Story 15.2 provider-neutral transaction contract coverage."""

import pytest

from twitclone.support_transactions import (
    SupportFeeBreakdown,
    SupportPayoutStatus,
    SupportReceiptContract,
    SupportTransactionStatus,
    can_transition_payout,
    can_transition_transaction,
)


def test_fee_breakdown_reconciles_gross_amount():
    breakdown = SupportFeeBreakdown(
        gross_amount_cents=1000,
        platform_fee_cents=50,
        provider_fee_cents=59,
        creator_net_cents=891,
    )
    assert breakdown.validate() is breakdown


@pytest.mark.parametrize(
    "kwargs",
    [
        {"gross_amount_cents": 99, "platform_fee_cents": 0, "provider_fee_cents": 0, "creator_net_cents": 99},
        {"gross_amount_cents": 100001, "platform_fee_cents": 0, "provider_fee_cents": 0, "creator_net_cents": 100001},
        {"gross_amount_cents": 1000, "platform_fee_cents": -1, "provider_fee_cents": 60, "creator_net_cents": 941},
        {"gross_amount_cents": 1000, "platform_fee_cents": 50, "provider_fee_cents": 50, "creator_net_cents": 850},
        {"gross_amount_cents": 1000, "platform_fee_cents": 50, "provider_fee_cents": 50, "creator_net_cents": 900, "currency": "EUR"},
    ],
)
def test_fee_breakdown_rejects_invalid_contract(kwargs):
    with pytest.raises(ValueError):
        SupportFeeBreakdown(**kwargs).validate()


def test_transaction_transition_contract_prevents_history_rewrite():
    assert can_transition_transaction("created", "pending") is True
    assert can_transition_transaction("pending", "succeeded") is True
    assert can_transition_transaction("succeeded", "refunded") is True
    assert can_transition_transaction("succeeded", "chargeback") is True
    assert can_transition_transaction("failed", "succeeded") is False
    assert can_transition_transaction("refunded", "succeeded") is False


def test_payout_transition_contract_is_separate_and_recoverable():
    assert can_transition_payout("not_ready", "pending") is True
    assert can_transition_payout("pending", "failed") is True
    assert can_transition_payout("failed", "pending") is True
    assert can_transition_payout("pending", "paid") is True
    assert can_transition_payout("paid", "reversed") is True
    assert can_transition_payout("reversed", "paid") is False


def test_receipt_contract_requires_reference_and_reconciled_fees():
    receipt = SupportReceiptContract(
        transaction_reference="ripple-support-123",
        creator_user_id=7,
        gross_amount_cents=2500,
        currency="USD",
        platform_fee_cents=125,
        provider_fee_cents=75,
        creator_net_cents=2300,
        status=SupportTransactionStatus.SUCCEEDED,
    )
    assert receipt.validate() is receipt

    with pytest.raises(ValueError):
        SupportReceiptContract(
            transaction_reference=" ",
            creator_user_id=7,
            gross_amount_cents=2500,
            currency="USD",
            platform_fee_cents=125,
            provider_fee_cents=75,
            creator_net_cents=2300,
            status=SupportTransactionStatus.SUCCEEDED,
        ).validate()


def test_contract_exposes_expected_terminal_states():
    assert SupportTransactionStatus.FAILED.value == "failed"
    assert SupportTransactionStatus.CANCELED.value == "canceled"
    assert SupportTransactionStatus.CHARGEBACK.value == "chargeback"
    assert SupportPayoutStatus.REVERSED.value == "reversed"
