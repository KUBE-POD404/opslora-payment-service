from sqlalchemy import Column, Integer, Numeric, String, DateTime, CheckConstraint, Text
from datetime import datetime, timezone
from app.database import Base

class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)

    organization_id = Column(Integer, nullable=False, index=True)
    # Plain reference (no FK)
    invoice_id = Column(Integer, nullable=False)

    amount = Column(Numeric(10, 2), nullable=False)
    payment_method = Column(String(20), nullable=False)
    created_by_user_id = Column(Integer, nullable=True)
    paid_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc))
    note = Column(Text, nullable=True)

    __table_args__ = (
        CheckConstraint("amount > 0", name="check_payment_amount_positive"),
        CheckConstraint(
            "payment_method IN ('CASH','CARD','UPI','BANK_TRANSFER')",
            name="check_payment_method"
        ),
    )