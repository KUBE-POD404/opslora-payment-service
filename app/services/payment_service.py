from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import func
import os
import logging

from app.models.payment import Payment
from app.exceptions.custom_exceptions import NotFoundException, ConflictException
from app.utils.service_client import authenticated_get, authenticated_post
from app.core.logging_config import request_id_ctx

INVOICE_SERVICE_URL = os.getenv("INVOICE_SERVICE_URL")
API_VERSION = os.getenv("API_VERSION", "/api/v1")

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

    return response.json()


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
    auth_header: str
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

    invoice_data = fetch_invoice(invoice_id, auth_header)

    if invoice_data["status"] == "CANCELLED":
        logger.warning("Attempt to pay cancelled invoice", extra={"invoice_id": invoice_id})
        raise ConflictException("Cannot pay a cancelled invoice")

    if invoice_data["status"] == "PAID":
        logger.warning("Invoice already paid", extra={"invoice_id": invoice_id})
        raise ConflictException("Invoice already fully paid")

    if amount <= Decimal("0.00"):
        logger.warning("Invalid payment amount", extra={"amount": str(amount)})
        raise ConflictException("Payment amount must be greater than zero")

    invoice_total = Decimal(str(invoice_data["total"]))

    total_paid = (
        db.query(func.coalesce(func.sum(Payment.amount), 0))
        .filter(
            Payment.invoice_id == invoice_id,
            Payment.organization_id == organization_id
        )
        .scalar()
    )

    total_paid = Decimal(str(total_paid))

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
        amount=amount,
        payment_method=payment_method,
        created_by_user_id=created_by_user_id,
        paid_at=datetime.now(timezone.utc),
    )

    db.add(payment)
    db.flush()

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


# -----------------------------
# REFUND
# -----------------------------
def refund_invoice(
    db: Session,
    invoice_id: int,
    organization_id: int,
    auth_header: str
):

    logger.info(
        "Initiating refund",
        extra={"invoice_id": invoice_id}
    )

    invoice_data = fetch_invoice(invoice_id, auth_header)

    if invoice_data["status"] != "PAID":
        logger.warning("Refund attempted on non-paid invoice", extra={"invoice_id": invoice_id})
        raise ConflictException("Refund allowed only for fully paid invoices")

    invoice_total = Decimal(str(invoice_data["total"]))

    total_paid = (
        db.query(func.coalesce(func.sum(Payment.amount), 0))
        .filter(
            Payment.invoice_id == invoice_id,
            Payment.organization_id == organization_id
        )
        .scalar()
    )

    total_paid = Decimal(str(total_paid))

    if total_paid != invoice_total:
        logger.warning("Invoice not fully paid", extra={"invoice_id": invoice_id})
        raise ConflictException("Invoice is not fully paid")

    update_invoice_status(invoice_id, "REFUNDED", auth_header)

    logger.info(
        "Refund completed",
        extra={
            "invoice_id": invoice_id,
            "amount": str(invoice_total)
        }
    )

    return {
        "invoice_id": invoice_id,
        "status": "REFUNDED"
    }