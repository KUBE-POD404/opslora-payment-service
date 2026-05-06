from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from typing import Optional

class PaymentCreate(BaseModel):
    invoice_id: int
    amount: float = Field(..., gt=0)
    payment_method: str = Field(..., pattern="^(CASH|CARD|UPI|BANK_TRANSFER|CHEQUE|ONLINE)$")
    currency: str = Field(default="INR", min_length=3, max_length=3)
    reference_number: Optional[str] = Field(default=None, max_length=100)
    gateway_provider: Optional[str] = Field(default=None, max_length=50)
    gateway_order_id: Optional[str] = Field(default=None, max_length=150)
    gateway_payment_id: Optional[str] = Field(default=None, max_length=150)
    gateway_signature: Optional[str] = Field(default=None, max_length=255)
    note: Optional[str] = None

class PaymentResponse(BaseModel):
    id: int
    invoice_id: int
    customer_id: Optional[int] = None
    amount: float
    currency: str
    payment_method: str
    payment_type: str
    status: str
    reference_number: Optional[str] = None
    gateway_provider: Optional[str] = None
    gateway_order_id: Optional[str] = None
    gateway_payment_id: Optional[str] = None
    paid_at: datetime
    note: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class PaymentTransactionResponse(BaseModel):
    id: int
    payment_id: Optional[int] = None
    invoice_id: int
    event_type: str
    status: str
    amount: Optional[float] = None
    currency: str
    provider: Optional[str] = None
    provider_event_id: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class RefundCreate(BaseModel):
    amount: Optional[float] = Field(default=None, gt=0)
    reason: Optional[str] = None
    gateway_refund_id: Optional[str] = Field(default=None, max_length=150)

class RefundResponse(BaseModel):
    id: int
    payment_id: Optional[int] = None
    invoice_id: int
    amount: float
    currency: str
    status: str
    refunded_at: datetime

    model_config = ConfigDict(from_attributes=True)
