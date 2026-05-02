from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.dependencies.auth import get_current_user
from app.main import app
from app.models.payment import Payment  # noqa: F401
from app.security.jwt import TokenPayload


def test_payment_api_partial_full_list_and_refund(monkeypatch):
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)

    invoice_state = {"status": "UNPAID", "total": 300.0}
    status_updates = []

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    def override_current_user():
        return TokenPayload(
            user_id=10,
            org_id=20,
            permissions=["payment.create", "payment.read", "payment.refund"],
        )

    def fake_fetch_invoice(invoice_id, auth_header):
        return {
            "id": invoice_id,
            "status": invoice_state["status"],
            "total": invoice_state["total"],
        }

    def fake_update_invoice_status(invoice_id, status, auth_header):
        status_updates.append(status)
        invoice_state["status"] = status

    monkeypatch.setattr("app.services.payment_service.fetch_invoice", fake_fetch_invoice)
    monkeypatch.setattr("app.services.payment_service.update_invoice_status", fake_update_invoice_status)

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_current_user

    try:
        client = TestClient(app)

        partial_response = client.post(
            "/api/v1/payments/pay",
            json={"invoice_id": 101, "amount": 100, "payment_method": "UPI"},
        )
        assert partial_response.status_code == 201
        assert partial_response.json()["amount"] == 100.0
        assert status_updates == ["PARTIALLY_PAID"]

        full_response = client.post(
            "/api/v1/payments/pay",
            json={"invoice_id": 101, "amount": 200, "payment_method": "BANK_TRANSFER"},
        )
        assert full_response.status_code == 201
        assert full_response.json()["amount"] == 200.0
        assert status_updates == ["PARTIALLY_PAID", "PAID"]

        list_response = client.get("/api/v1/payments/invoice/101")
        assert list_response.status_code == 200
        assert [payment["amount"] for payment in list_response.json()] == [100.0, 200.0]

        refund_response = client.post("/api/v1/payments/refund/101")
        assert refund_response.status_code == 200
        assert refund_response.json() == {"invoice_id": 101, "status": "REFUNDED"}
        assert status_updates[-1] == "REFUNDED"
    finally:
        app.dependency_overrides.clear()
        Base.metadata.drop_all(bind=engine)
