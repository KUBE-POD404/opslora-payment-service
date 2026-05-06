from sqlalchemy import Column, Integer, Numeric, String, DateTime, CheckConstraint, Text
from datetime import datetime, timezone
from app.database import Base

class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)

    organization_id = Column(Integer, nullable=False, index=True)
    # Plain reference (no FK)
    invoice_id = Column(Integer, nullable=False)
    customer_id = Column(Integer, nullable=True, index=True)

    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), nullable=False, default="INR")
    payment_method = Column(String(20), nullable=False)
    payment_type = Column(String(20), nullable=False, default="MANUAL")
    status = Column(String(30), nullable=False, default="SUCCEEDED")
    reference_number = Column(String(100), nullable=True)
    gateway_provider = Column(String(50), nullable=True)
    gateway_order_id = Column(String(150), nullable=True)
    gateway_payment_id = Column(String(150), nullable=True)
    gateway_signature = Column(String(255), nullable=True)
    failure_reason = Column(Text, nullable=True)
    metadata_json = Column(Text, nullable=True)
    created_by_user_id = Column(Integer, nullable=True)
    received_by_user_id = Column(Integer, nullable=True)
    paid_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc))
    note = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc))

    __table_args__ = (
        CheckConstraint("amount > 0", name="check_payment_amount_positive"),
        CheckConstraint(
            "payment_method IN ('CASH','CARD','UPI','BANK_TRANSFER','CHEQUE','ONLINE')",
            name="check_payment_method"
        ),
        CheckConstraint(
            "payment_type IN ('MANUAL','GATEWAY')",
            name="check_payment_type"
        ),
        CheckConstraint(
            "status IN ('PENDING','PROCESSING','SUCCEEDED','FAILED','CANCELLED','REFUNDED','PARTIALLY_REFUNDED')",
            name="check_payment_status"
        ),
    )


class PaymentTransaction(Base):
    __tablename__ = "payment_transactions"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, nullable=False, index=True)
    payment_id = Column(Integer, nullable=True, index=True)
    invoice_id = Column(Integer, nullable=False, index=True)
    event_type = Column(String(40), nullable=False)
    status = Column(String(30), nullable=False)
    amount = Column(Numeric(10, 2), nullable=True)
    currency = Column(String(3), nullable=False, default="INR")
    provider = Column(String(50), nullable=True)
    provider_event_id = Column(String(150), nullable=True)
    raw_payload_json = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc))

    __table_args__ = (
        CheckConstraint(
            "event_type IN ('CREATED','AUTHORIZED','CAPTURED','FAILED','REFUND_CREATED','REFUNDED','WEBHOOK_RECEIVED')",
            name="check_payment_transaction_event_type"
        ),
        CheckConstraint(
            "status IN ('PENDING','PROCESSING','SUCCEEDED','FAILED','CANCELLED','REFUNDED','PARTIALLY_REFUNDED')",
            name="check_payment_transaction_status"
        ),
    )


class Refund(Base):
    __tablename__ = "refunds"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, nullable=False, index=True)
    payment_id = Column(Integer, nullable=True, index=True)
    invoice_id = Column(Integer, nullable=False, index=True)
    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), nullable=False, default="INR")
    status = Column(String(30), nullable=False, default="SUCCEEDED")
    reason = Column(Text, nullable=True)
    gateway_refund_id = Column(String(150), nullable=True)
    refunded_by_user_id = Column(Integer, nullable=True)
    refunded_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc))
    created_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc))

    __table_args__ = (
        CheckConstraint("amount > 0", name="check_refund_amount_positive"),
        CheckConstraint(
            "status IN ('PENDING','PROCESSING','SUCCEEDED','FAILED','CANCELLED')",
            name="check_refund_status"
        ),
    )
