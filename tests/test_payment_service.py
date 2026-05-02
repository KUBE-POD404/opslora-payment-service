from decimal import Decimal

import pytest

from app.exceptions.custom_exceptions import ConflictException
from app.services import payment_service


def test_partial_and_full_payment_status_updates(db_session, monkeypatch):
    invoice = {"id": 1, "total": "100.00", "status": "UNPAID"}
    statuses = []

    def fetch_invoice(invoice_id, auth_header):
        return invoice

    def update_invoice_status(invoice_id, status, auth_header):
        statuses.append(status)
        invoice["status"] = status

    monkeypatch.setattr(payment_service, "fetch_invoice", fetch_invoice)
    monkeypatch.setattr(payment_service, "update_invoice_status", update_invoice_status)

    first = payment_service.create_payment(db_session, 1, Decimal("40.00"), "UPI", 1, 10, "Bearer token")
    second = payment_service.create_payment(
        db_session, 1, Decimal("60.00"), "BANK_TRANSFER", 1, 10, "Bearer token"
    )

    assert first.amount == Decimal("40.00")
    assert second.amount == Decimal("60.00")
    assert statuses == ["PARTIALLY_PAID", "PAID"]


def test_payment_cannot_exceed_invoice_total(db_session, monkeypatch):
    monkeypatch.setattr(
        payment_service,
        "fetch_invoice",
        lambda invoice_id, auth_header: {"id": 1, "total": "100.00", "status": "UNPAID"},
    )
    monkeypatch.setattr(payment_service, "update_invoice_status", lambda *args, **kwargs: None)
    payment_service.create_payment(db_session, 1, Decimal("80.00"), "UPI", 1, 10, "Bearer token")

    with pytest.raises(ConflictException):
        payment_service.create_payment(db_session, 1, Decimal("30.00"), "UPI", 1, 10, "Bearer token")


def test_refund_requires_fully_paid_invoice(db_session, monkeypatch):
    monkeypatch.setattr(
        payment_service,
        "fetch_invoice",
        lambda invoice_id, auth_header: {"id": 1, "total": "100.00", "status": "PARTIALLY_PAID"},
    )

    with pytest.raises(ConflictException):
        payment_service.refund_invoice(db_session, 1, 1, "Bearer token")


def test_refund_updates_invoice_status_when_fully_paid(db_session, monkeypatch):
    statuses = []
    monkeypatch.setattr(
        payment_service,
        "fetch_invoice",
        lambda invoice_id, auth_header: {"id": 1, "total": "100.00", "status": "UNPAID"},
    )
    monkeypatch.setattr(payment_service, "update_invoice_status", lambda *args: statuses.append(args[1]))
    payment_service.create_payment(db_session, 1, Decimal("100.00"), "UPI", 1, 10, "Bearer token")

    monkeypatch.setattr(
        payment_service,
        "fetch_invoice",
        lambda invoice_id, auth_header: {"id": 1, "total": "100.00", "status": "PAID"},
    )
    refund = payment_service.refund_invoice(db_session, 1, 1, "Bearer token")

    assert refund == {"invoice_id": 1, "status": "REFUNDED"}
    assert statuses[-1] == "REFUNDED"
