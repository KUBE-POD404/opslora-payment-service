from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime

class PaymentCreate(BaseModel):
    invoice_id: int
    amount: float = Field(..., gt=0)
    payment_method: str = Field(..., pattern="^(CASH|CARD|UPI|BANK_TRANSFER)$")

class PaymentResponse(BaseModel):
    id: int
    invoice_id: int
    amount: float
    payment_method: str
    paid_at: datetime

    model_config = ConfigDict(from_attributes=True)

class RefundResponse(BaseModel):
    invoice_id: int
    status: str
    refunded_at: datetime