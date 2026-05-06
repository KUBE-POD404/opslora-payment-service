from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import func
import logging

from app.models.payment import Payment, PaymentTransaction, Refund
from app.exceptions.custom_exceptions import NotFoundException, ConflictException
from app.utils.service_client import authenticated_get, authenticated_post
from app.core.logging_config import request_id_ctx
from app.core.config import settings

INVOICE_SERVICE_URL = settings.invoice_service_url
API_VERSION = settings.api_version

logger = logging.getLogger(__name__)


# -----------------------------
# FETCH INVOICE
# -----------------------------
def fetch_invoice(invoice_id: int, auth_header: str):

    url = f"{INVOICE_SERVICE_URL}{API_VERSION}/invoices/{invoice_id}"

    logger.info(
        "Fetching invoice",
        extra={"invoice_id": invoice_id, "url": url}
    )

    response = authenticated_get(url, auth_header)

    logger.info(
        "Invoice service response",
        extra={
            "invoice_id": invoice_id,
            "status_code": response.status_code
        }
    )

    if response.status_code == 404:
        logger.warning("Invoice not found", extra={"invoice_id": invoice_id})
        raise NotFoundException("Invoice not found")

    if response.status_code != 200:
        logger.error(
            "Failed to fetch invoice",
            extra={"invoice_id": invoice_id, "status_code": response.status_code}
        )
        raise ConflictException("Failed to fetch invoice")

    data = response.json()
    if data.get("id") is None or data.get("status") in (None, "") or data.get("total") is None:
        raise ConflictException("Invalid invoice service response")

    return data


# -----------------------------
# UPDATE INVOICE STATUS
# -----------------------------
def update_invoice_status(invoice_id: int, status: str, auth_header: str):

    url = f"{INVOICE_SERVICE_URL}{API_VERSION}/invoices/{invoice_id}/status"

    logger.info(
        "Updating invoice status",
        extra={"invoice_id": invoice_id, "status": status}
    )

    response = authenticated_post(
        url,
        auth_header,
        json={"status": status}
    )

    if response.status_code not in (200, 201):
        logger.error(
            "Failed to update invoice status",
            extra={
                "invoice_id": invoice_id,
                "status": status,
                "status_code": response.status_code
            }
        )
        raise ConflictException("Failed to update invoice status")

    logger.info(
        "Invoice status updated successfully",
        extra={"invoice_id": invoice_id, "status": status}
    )


def _successful_payment_total(db: Session, invoice_id: int, organization_id: int) -> Decimal:
    total_paid = (
        db.query(func.coalesce(func.sum(Payment.amount), 0))
        .filter(
            Payment.invoice_id == invoice_id,
            Payment.organization_id == organization_id,
            Payment.status.in_(("SUCCEEDED", "PARTIALLY_REFUNDED", "REFUNDED")),
        )
        .scalar()
    )
    return Decimal(str(total_paid))


def _refunded_total(db: Session, invoice_id: int, organization_id: int) -> Decimal:
    total_refunded = (
        db.query(func.coalesce(func.sum(Refund.amount), 0))
        .filter(
            Refund.invoice_id == invoice_id,
            Refund.organization_id == organization_id,
            Refund.status == "SUCCEEDED",
        )
        .scalar()
    )
    return Decimal(str(total_refunded))


def _record_transaction(
    db: Session,
    *,
    organization_id: int,
    invoice_id: int,
    event_type: str,
    status: str,
    amount: Decimal | None = None,
    currency: str = "INR",
    payment_id: int | None = None,
    provider: str | None = None,
    provider_event_id: str | None = None,
    raw_payload_json: str | None = None,
) -> PaymentTransaction:
    transaction = PaymentTransaction(
        organization_id=organization_id,
        payment_id=payment_id,
        invoice_id=invoice_id,
        event_type=event_type,
        status=status,
        amount=amount,
        currency=currency,
        provider=provider,
        provider_event_id=provider_event_id,
        raw_payload_json=raw_payload_json,
        created_at=datetime.now(timezone.utc),
    )
    db.add(transaction)
    return transaction


# -----------------------------
# CREATE PAYMENT
# -----------------------------
def create_payment(
    db: Session,
    invoice_id: int,
    amount: Decimal,
    payment_method: str,
    organization_id: int,
    created_by_user_id: int,
    auth_header: str,
    currency: str = "INR",
    reference_number: str | None = None,
    gateway_provider: str | None = None,
    gateway_order_id: str | None = None,
    gateway_payment_id: str | None = None,
    gateway_signature: str | None = None,
    note: str | None = None,
):

    logger.info(
        "Creating payment",
        extra={
            "invoice_id": invoice_id,
            "amount": str(amount),
            "payment_method": payment_method
        }
    )

    amount = Decimal(str(amount))
    currency = currency.upper()

    invoice_data = fetch_invoice(invoice_id, auth_header)

    if invoice_data["status"] in ("CANCELLED", "REFUNDED"):
        logger.warning("Attempt to pay cancelled invoice", extra={"invoice_id": invoice_id})
        raise ConflictException("Cannot pay this invoice")

    if invoice_data["status"] == "PAID":
        logger.warning("Invoice already paid", extra={"invoice_id": invoice_id})
        raise ConflictException("Invoice already fully paid")

    if amount <= Decimal("0.00"):
        logger.warning("Invalid payment amount", extra={"amount": str(amount)})
        raise ConflictException("Payment amount must be greater than zero")

    invoice_total = Decimal(str(invoice_data["total"]))

    total_paid = _successful_payment_total(db, invoice_id, organization_id) - _refunded_total(
        db, invoice_id, organization_id
    )

    logger.info(
        "Payment validation",
        extra={
            "invoice_id": invoice_id,
            "invoice_total": str(invoice_total),
            "current_paid": str(total_paid),
            "incoming_amount": str(amount)
        }
    )

    if total_paid + amount > invoice_total:
        logger.warning("Payment exceeds invoice total", extra={"invoice_id": invoice_id})
        raise ConflictException("Payment exceeds invoice total")

    payment = Payment(
        organization_id=organization_id,
        invoice_id=invoice_id,
        customer_id=invoice_data.get("customer_id"),
        amount=amount,
        currency=currency,
        payment_method=payment_method,
        payment_type="GATEWAY" if payment_method == "ONLINE" or gateway_provider else "MANUAL",
        status="SUCCEEDED",
        reference_number=reference_number,
        gateway_provider=gateway_provider,
        gateway_order_id=gateway_order_id,
        gateway_payment_id=gateway_payment_id,
        gateway_signature=gateway_signature,
        created_by_user_id=created_by_user_id,
        received_by_user_id=created_by_user_id,
        paid_at=datetime.now(timezone.utc),
        note=note,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    db.add(payment)
    db.flush()
    _record_transaction(
        db,
        organization_id=organization_id,
        payment_id=payment.id,
        invoice_id=invoice_id,
        event_type="CAPTURED",
        status="SUCCEEDED",
        amount=amount,
        currency=currency,
        provider=gateway_provider,
        provider_event_id=gateway_payment_id or reference_number,
    )

    new_total_paid = total_paid + amount

    if new_total_paid == invoice_total:
        new_status = "PAID"
    else:
        new_status = "PARTIALLY_PAID"

    logger.info(
        "Determined invoice status",
        extra={
            "invoice_id": invoice_id,
            "new_status": new_status
        }
    )

    update_invoice_status(invoice_id, new_status, auth_header)

    db.commit()
    db.refresh(payment)

    logger.info(
        "Payment created successfully",
        extra={
            "payment_id": payment.id,
            "invoice_id": invoice_id,
            "amount": str(amount)
        }
    )

    return payment


def list_payments(
    db: Session,
    organization_id: int,
    invoice_id: int | None = None,
    customer_id: int | None = None,
    status: str | None = None,
    payment_method: str | None = None,
) -> list[Payment]:
    query = db.query(Payment).filter(Payment.organization_id == organization_id)

    if invoice_id is not None:
        query = query.filter(Payment.invoice_id == invoice_id)
    if customer_id is not None:
        query = query.filter(Payment.customer_id == customer_id)
    if status:
        query = query.filter(Payment.status == status)
    if payment_method:
        query = query.filter(Payment.payment_method == payment_method)

    return query.order_by(Payment.paid_at.desc(), Payment.id.desc()).all()


# -----------------------------
# GET PAYMENTS FOR INVOICE
# -----------------------------
def get_payments_for_invoice(
    db: Session,
    invoice_id: int,
    organization_id: int,
    auth_header: str
):

    logger.info(
        "Fetching payments for invoice",
        extra={"invoice_id": invoice_id}
    )

    fetch_invoice(invoice_id, auth_header)

    payments = (
        db.query(Payment)
        .filter(
            Payment.invoice_id == invoice_id,
            Payment.organization_id == organization_id
        )
        .order_by(Payment.paid_at.asc())
        .all()
    )

    logger.info(
        "Payments fetched",
        extra={
            "invoice_id": invoice_id,
            "count": len(payments)
        }
    )

    return payments


def get_transactions_for_payment(
    db: Session,
    payment_id: int,
    organization_id: int,
) -> list[PaymentTransaction]:
    payment = (
        db.query(Payment)
        .filter(Payment.id == payment_id, Payment.organization_id == organization_id)
        .first()
    )
    if not payment:
        raise NotFoundException("Payment not found")

    return (
        db.query(PaymentTransaction)
        .filter(
            PaymentTransaction.payment_id == payment_id,
            PaymentTransaction.organization_id == organization_id,
        )
        .order_by(PaymentTransaction.created_at.asc(), PaymentTransaction.id.asc())
        .all()
    )


# -----------------------------
# REFUND
# -----------------------------
def refund_payment(
    db: Session,
    payment_id: int,
    organization_id: int,
    refunded_by_user_id: int,
    auth_header: str,
    amount: Decimal | None = None,
    reason: str | None = None,
    gateway_refund_id: str | None = None,
):

    logger.info(
        "Initiating refund",
        extra={"payment_id": payment_id}
    )

    payment = (
        db.query(Payment)
        .filter(Payment.id == payment_id, Payment.organization_id == organization_id)
        .first()
    )
    if not payment:
        raise NotFoundException("Payment not found")

    invoice_id = payment.invoice_id
    invoice_data = fetch_invoice(invoice_id, auth_header)

    if invoice_data["status"] not in ("PAID", "PARTIALLY_PAID"):
        logger.warning("Refund attempted on non-paid invoice", extra={"invoice_id": invoice_id})
        raise ConflictException("Refund allowed only for paid invoices")

    refund_amount = Decimal(str(amount)) if amount is not None else Decimal(str(payment.amount))
    already_refunded = (
        db.query(func.coalesce(func.sum(Refund.amount), 0))
        .filter(
            Refund.payment_id == payment.id,
            Refund.organization_id == organization_id,
            Refund.status == "SUCCEEDED",
        )
        .scalar()
    )
    already_refunded = Decimal(str(already_refunded))

    if refund_amount <= Decimal("0.00"):
        raise ConflictException("Refund amount must be greater than zero")

    if already_refunded + refund_amount > Decimal(str(payment.amount)):
        raise ConflictException("Refund exceeds payment amount")

    refund = Refund(
        organization_id=organization_id,
        payment_id=payment.id,
        invoice_id=invoice_id,
        amount=refund_amount,
        currency=payment.currency,
        status="SUCCEEDED",
        reason=reason,
        gateway_refund_id=gateway_refund_id,
        refunded_by_user_id=refunded_by_user_id,
        refunded_at=datetime.now(timezone.utc),
        created_at=datetime.now(timezone.utc),
    )
    db.add(refund)
    db.flush()

    payment_refunded_total = already_refunded + refund_amount
    if payment_refunded_total == Decimal(str(payment.amount)):
        payment.status = "REFUNDED"
    else:
        payment.status = "PARTIALLY_REFUNDED"
    payment.updated_at = datetime.now(timezone.utc)

    _record_transaction(
        db,
        organization_id=organization_id,
        payment_id=payment.id,
        invoice_id=invoice_id,
        event_type="REFUNDED",
        status="SUCCEEDED",
        amount=refund_amount,
        currency=payment.currency,
        provider=payment.gateway_provider,
        provider_event_id=gateway_refund_id,
    )

    net_paid = _successful_payment_total(db, invoice_id, organization_id) - _refunded_total(
        db, invoice_id, organization_id
    )

    if net_paid <= Decimal("0.00"):
        new_status = "REFUNDED"
    else:
        new_status = "PARTIALLY_PAID"

    update_invoice_status(invoice_id, new_status, auth_header)
    db.commit()
    db.refresh(refund)

    logger.info(
        "Refund completed",
        extra={
            "invoice_id": invoice_id,
            "payment_id": payment.id,
            "amount": str(refund_amount)
        }
    )

    return refund


def refund_invoice(
    db: Session,
    invoice_id: int,
    organization_id: int,
    refunded_by_user_id: int,
    auth_header: str,
    reason: str | None = None,
):
    payments = (
        db.query(Payment)
        .filter(
            Payment.invoice_id == invoice_id,
            Payment.organization_id == organization_id,
            Payment.status.in_(("SUCCEEDED", "PARTIALLY_REFUNDED", "REFUNDED")),
        )
        .order_by(Payment.paid_at.desc(), Payment.id.desc())
        .all()
    )
    if not payments:
        raise NotFoundException("Payment not found")

    last_refund = None
    for payment in payments:
        refunded_amount = (
            db.query(func.coalesce(func.sum(Refund.amount), 0))
            .filter(
                Refund.payment_id == payment.id,
                Refund.organization_id == organization_id,
                Refund.status == "SUCCEEDED",
            )
            .scalar()
        )
        remaining = Decimal(str(payment.amount)) - Decimal(str(refunded_amount))
        if remaining > Decimal("0.00"):
            last_refund = refund_payment(
                db,
                payment.id,
                organization_id,
                refunded_by_user_id,
                auth_header,
                amount=remaining,
                reason=reason,
            )

    if not last_refund:
        raise ConflictException("Invoice is already fully refunded")

    return last_refund
