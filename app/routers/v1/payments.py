from fastapi import APIRouter, Depends, status, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import PaymentCreate, PaymentResponse

from app.services.payment_service import (
    create_payment,
    get_payments_for_invoice,
    refund_invoice
)

from app.dependencies.permissions import require_permission

router = APIRouter(prefix="/payments", tags=["Payments"])

@router.get("/health")
def health():
    return {"status": "ok"}


@router.post("/pay", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
def create_payment_api(
    payload: PaymentCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user = Depends(require_permission("payment.create"))
):

    auth_header = request.headers.get("Authorization")

    return create_payment(
        db=db,
        invoice_id=payload.invoice_id,
        amount=payload.amount,
        payment_method=payload.payment_method,
        organization_id=current_user.org_id,
        created_by_user_id=current_user.user_id,
        auth_header=auth_header
    )


@router.get("/invoice/{invoice_id}", response_model=list[PaymentResponse])
def get_payments_for_invoice_api(
    invoice_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user = Depends(require_permission("payment.read"))
):

    auth_header = request.headers.get("Authorization")

    return get_payments_for_invoice(
        db,
        invoice_id,
        current_user.org_id,
        auth_header
    )


@router.post("/refund/{invoice_id}")
def refund_invoice_api(
    invoice_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user = Depends(require_permission("payment.refund"))
):

    auth_header = request.headers.get("Authorization")

    return refund_invoice(
        db,
        invoice_id,
        current_user.org_id,
        auth_header
    )