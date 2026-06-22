from fastapi import APIRouter, Depends, status, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import PaymentCreate, PaymentResponse, PaymentTransactionResponse, RefundCreate, RefundResponse
from typing import Annotated

from app.services.payment_service import (
    create_payment,
    get_payments_for_invoice,
    get_transactions_for_payment,
    list_payments,
    refund_invoice,
    refund_payment,
)

from app.dependencies.permissions import require_permission

router = APIRouter(prefix="/payments", tags=["Payments"])

DBSession = Annotated[Session, Depends(get_db)]

@router.post("/pay", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
def create_payment_api(
    payload: PaymentCreate,
    request: Request,
    db: DBSession,
    current_user: Annotated[
        any,
        Depends(require_permission("payment.create"))
    ]
):

    auth_header = request.headers.get("Authorization")

    return create_payment(
        db=db,
        invoice_id=payload.invoice_id,
        amount=payload.amount,
        payment_method=payload.payment_method,
        organization_id=current_user.org_id,
        created_by_user_id=current_user.user_id,
        auth_header=auth_header,
        currency=payload.currency,
        reference_number=payload.reference_number,
        gateway_provider=payload.gateway_provider,
        gateway_order_id=payload.gateway_order_id,
        gateway_payment_id=payload.gateway_payment_id,
        gateway_signature=payload.gateway_signature,
        note=payload.note,
    )


@router.get("/", response_model=list[PaymentResponse])
def list_payment_api(
    db: DBSession,
    current_user: Annotated[
        any,
        Depends(require_permission("payment.read"))
    ],
    invoice_id: int | None = None,
    customer_id: int | None = None,
    status: str | None = None,
    payment_method: str | None = None,
):
    return list_payments(
        db,
        organization_id=current_user.org_id,
        invoice_id=invoice_id,
        customer_id=customer_id,
        status=status,
        payment_method=payment_method,
    )


@router.get("/invoice/{invoice_id}", response_model=list[PaymentResponse])
def get_payments_for_invoice_api(
    invoice_id: int,
    request: Request,
    db: DBSession,
    current_user: Annotated[
        any,
        Depends(require_permission("payment.read"))
    ]
):

    auth_header = request.headers.get("Authorization")

    return get_payments_for_invoice(
        db,
        invoice_id,
        current_user.org_id,
        auth_header
    )


@router.get("/{payment_id}/transactions", response_model=list[PaymentTransactionResponse])
def get_payment_transactions_api(
    payment_id: int,
    db: DBSession,
    current_user: Annotated[
        any,
        Depends(require_permission("payment.read"))
    ]
):
    return get_transactions_for_payment(db, payment_id, current_user.org_id)


@router.post("/{payment_id}/refund", response_model=RefundResponse)
def refund_payment_api(
    payment_id: int,
    payload: RefundCreate,
    request: Request,
    db: DBSession,
    current_user: Annotated[
        any,
        Depends(require_permission("payment.refund"))
    ]
):
    auth_header = request.headers.get("Authorization")

    return refund_payment(
        db,
        payment_id,
        current_user.org_id,
        current_user.user_id,
        auth_header,
        amount=payload.amount,
        reason=payload.reason,
        gateway_refund_id=payload.gateway_refund_id,
    )


@router.post("/refund/{invoice_id}", response_model=RefundResponse)
def refund_invoice_api(
    invoice_id: int,
    request: Request,
    db: DBSession,
    current_user: Annotated[
        any,
        Depends(require_permission("payment.refund"))
    ]
):

    auth_header = request.headers.get("Authorization")

    return refund_invoice(
        db,
        invoice_id,
        current_user.org_id,
        current_user.user_id,
        auth_header
    )
