"""payment transactions refunds

Revision ID: 20260506_payment_0002
Revises: 20260501_payment_0001
Create Date: 2026-05-06
"""

from alembic import op
import sqlalchemy as sa

revision = "20260506_payment_0002"
down_revision = "20260501_payment_0001"
branch_labels = None
depends_on = None


def upgrade():
    dialect_name = op.get_context().dialect.name
    if dialect_name != "sqlite":
        op.drop_constraint("check_payment_method", "payments", type_="check")

    op.add_column("payments", sa.Column("customer_id", sa.Integer(), nullable=True))
    op.add_column("payments", sa.Column("currency", sa.String(length=3), nullable=False, server_default="INR"))
    op.add_column("payments", sa.Column("payment_type", sa.String(length=20), nullable=False, server_default="MANUAL"))
    op.add_column("payments", sa.Column("status", sa.String(length=30), nullable=False, server_default="SUCCEEDED"))
    op.add_column("payments", sa.Column("reference_number", sa.String(length=100), nullable=True))
    op.add_column("payments", sa.Column("gateway_provider", sa.String(length=50), nullable=True))
    op.add_column("payments", sa.Column("gateway_order_id", sa.String(length=150), nullable=True))
    op.add_column("payments", sa.Column("gateway_payment_id", sa.String(length=150), nullable=True))
    op.add_column("payments", sa.Column("gateway_signature", sa.String(length=255), nullable=True))
    op.add_column("payments", sa.Column("failure_reason", sa.Text(), nullable=True))
    op.add_column("payments", sa.Column("metadata_json", sa.Text(), nullable=True))
    op.add_column("payments", sa.Column("received_by_user_id", sa.Integer(), nullable=True))
    op.add_column("payments", sa.Column("created_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("payments", sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True))
    op.create_index(op.f("ix_payments_customer_id"), "payments", ["customer_id"], unique=False)
    if dialect_name != "sqlite":
        op.create_check_constraint(
            "check_payment_method",
            "payments",
            "payment_method IN ('CASH','CARD','UPI','BANK_TRANSFER','CHEQUE','ONLINE')",
        )

    op.create_table(
        "payment_transactions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("organization_id", sa.Integer(), nullable=False),
        sa.Column("payment_id", sa.Integer(), nullable=True),
        sa.Column("invoice_id", sa.Integer(), nullable=False),
        sa.Column("event_type", sa.String(length=40), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("amount", sa.Numeric(10, 2), nullable=True),
        sa.Column("currency", sa.String(length=3), nullable=False, server_default="INR"),
        sa.Column("provider", sa.String(length=50), nullable=True),
        sa.Column("provider_event_id", sa.String(length=150), nullable=True),
        sa.Column("raw_payload_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "event_type IN ('CREATED','AUTHORIZED','CAPTURED','FAILED','REFUND_CREATED','REFUNDED','WEBHOOK_RECEIVED')",
            name="check_payment_transaction_event_type",
        ),
        sa.CheckConstraint(
            "status IN ('PENDING','PROCESSING','SUCCEEDED','FAILED','CANCELLED','REFUNDED','PARTIALLY_REFUNDED')",
            name="check_payment_transaction_status",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_payment_transactions_id"), "payment_transactions", ["id"], unique=False)
    op.create_index(op.f("ix_payment_transactions_invoice_id"), "payment_transactions", ["invoice_id"], unique=False)
    op.create_index(op.f("ix_payment_transactions_organization_id"), "payment_transactions", ["organization_id"], unique=False)
    op.create_index(op.f("ix_payment_transactions_payment_id"), "payment_transactions", ["payment_id"], unique=False)

    op.create_table(
        "refunds",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("organization_id", sa.Integer(), nullable=False),
        sa.Column("payment_id", sa.Integer(), nullable=True),
        sa.Column("invoice_id", sa.Integer(), nullable=False),
        sa.Column("amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False, server_default="INR"),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="SUCCEEDED"),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("gateway_refund_id", sa.String(length=150), nullable=True),
        sa.Column("refunded_by_user_id", sa.Integer(), nullable=True),
        sa.Column("refunded_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("amount > 0", name="check_refund_amount_positive"),
        sa.CheckConstraint(
            "status IN ('PENDING','PROCESSING','SUCCEEDED','FAILED','CANCELLED')",
            name="check_refund_status",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_refunds_id"), "refunds", ["id"], unique=False)
    op.create_index(op.f("ix_refunds_invoice_id"), "refunds", ["invoice_id"], unique=False)
    op.create_index(op.f("ix_refunds_organization_id"), "refunds", ["organization_id"], unique=False)
    op.create_index(op.f("ix_refunds_payment_id"), "refunds", ["payment_id"], unique=False)


def downgrade():
    dialect_name = op.get_context().dialect.name
    op.drop_index(op.f("ix_refunds_payment_id"), table_name="refunds")
    op.drop_index(op.f("ix_refunds_organization_id"), table_name="refunds")
    op.drop_index(op.f("ix_refunds_invoice_id"), table_name="refunds")
    op.drop_index(op.f("ix_refunds_id"), table_name="refunds")
    op.drop_table("refunds")

    op.drop_index(op.f("ix_payment_transactions_payment_id"), table_name="payment_transactions")
    op.drop_index(op.f("ix_payment_transactions_organization_id"), table_name="payment_transactions")
    op.drop_index(op.f("ix_payment_transactions_invoice_id"), table_name="payment_transactions")
    op.drop_index(op.f("ix_payment_transactions_id"), table_name="payment_transactions")
    op.drop_table("payment_transactions")

    if dialect_name != "sqlite":
        op.drop_constraint("check_payment_method", "payments", type_="check")
    op.drop_index(op.f("ix_payments_customer_id"), table_name="payments")
    op.drop_column("payments", "updated_at")
    op.drop_column("payments", "created_at")
    op.drop_column("payments", "received_by_user_id")
    op.drop_column("payments", "metadata_json")
    op.drop_column("payments", "failure_reason")
    op.drop_column("payments", "gateway_signature")
    op.drop_column("payments", "gateway_payment_id")
    op.drop_column("payments", "gateway_order_id")
    op.drop_column("payments", "gateway_provider")
    op.drop_column("payments", "reference_number")
    op.drop_column("payments", "status")
    op.drop_column("payments", "payment_type")
    op.drop_column("payments", "currency")
    op.drop_column("payments", "customer_id")
    if dialect_name != "sqlite":
        op.create_check_constraint(
            "check_payment_method",
            "payments",
            "payment_method IN ('CASH','CARD','UPI','BANK_TRANSFER')",
        )
