import pytest

from app.exceptions.custom_exceptions import ConflictException, NotFoundException
from app.services import payment_service


class FakeResponse:
    def __init__(self, status_code, payload):
        self.status_code = status_code
        self._payload = payload

    def json(self):
        return self._payload


def test_invoice_contract_accepts_required_invoice_shape(monkeypatch):
    calls = []

    def fake_get(url, auth_header):
        calls.append((url, auth_header))
        return FakeResponse(
            200,
            {"id": 101, "status": "UNPAID", "total": "295.00"},
        )

    monkeypatch.setattr(payment_service, "authenticated_get", fake_get)

    invoice = payment_service.fetch_invoice(101, "Bearer token")

    assert invoice == {"id": 101, "status": "UNPAID", "total": "295.00"}
    assert calls == [
        ("http://invoice-service:3000/api/v1/invoices/101", "Bearer token")
    ]


def test_invoice_contract_missing_invoice_returns_not_found(monkeypatch):
    monkeypatch.setattr(
        payment_service,
        "authenticated_get",
        lambda *_args: FakeResponse(404, {"error": {"code": "NOT_FOUND"}}),
    )

    with pytest.raises(NotFoundException):
        payment_service.fetch_invoice(101, "Bearer token")


@pytest.mark.parametrize(
    "payload",
    [
        {"status": "UNPAID", "total": "295.00"},
        {"id": 101, "total": "295.00"},
        {"id": 101, "status": "UNPAID"},
    ],
)
def test_invoice_contract_rejects_incomplete_success_payload(monkeypatch, payload):
    monkeypatch.setattr(
        payment_service,
        "authenticated_get",
        lambda *_args: FakeResponse(200, payload),
    )

    with pytest.raises(ConflictException):
        payment_service.fetch_invoice(101, "Bearer token")


@pytest.mark.parametrize("status", ["PARTIALLY_PAID", "PAID", "REFUNDED"])
def test_invoice_status_update_contract_accepts_payment_statuses(monkeypatch, status):
    calls = []

    def fake_post(url, auth_header, json):
        calls.append((url, auth_header, json))
        return FakeResponse(200, {"status": json["status"]})

    monkeypatch.setattr(payment_service, "authenticated_post", fake_post)

    payment_service.update_invoice_status(101, status, "Bearer token")

    assert calls == [
        (
            "http://invoice-service:3000/api/v1/invoices/101/status",
            "Bearer token",
            {"status": status},
        )
    ]


def test_invoice_status_update_contract_rejects_failed_update(monkeypatch):
    monkeypatch.setattr(
        payment_service,
        "authenticated_post",
        lambda *_args, **_kwargs: FakeResponse(409, {"error": {"code": "CONFLICT"}}),
    )

    with pytest.raises(ConflictException):
        payment_service.update_invoice_status(101, "PAID", "Bearer token")
