from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001_initial_schema"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("telegram_id", sa.BigInteger(), nullable=False),
        sa.Column("username", sa.String(length=255), nullable=True),
        sa.Column("first_name", sa.String(length=255), nullable=True),
        sa.Column("last_name", sa.String(length=255), nullable=True),
        sa.Column("balance_kopecks", sa.Integer(), nullable=False),
        sa.Column("max_vpn_keys", sa.Integer(), nullable=False),
        sa.Column("blocked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_telegram_id"), "users", ["telegram_id"], unique=True)

    op.create_table(
        "payments",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("provider", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("amount_kopecks", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("invoice_payload", sa.String(length=255), nullable=False),
        sa.Column("telegram_payment_charge_id", sa.String(length=255), nullable=True),
        sa.Column("provider_payment_charge_id", sa.String(length=255), nullable=True),
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_payments_user_id"), "payments", ["user_id"], unique=False)
    op.create_unique_constraint("uq_payments_invoice_payload", "payments", ["invoice_payload"])
    op.create_unique_constraint("uq_payments_provider_payment_charge_id", "payments", ["provider_payment_charge_id"])
    op.create_unique_constraint("uq_payments_telegram_payment_charge_id", "payments", ["telegram_payment_charge_id"])

    op.create_table(
        "vpn_accesses",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(length=100), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("managed_by", sa.String(length=32), nullable=False),
        sa.Column("xray_inbound_tag", sa.String(length=255), nullable=False),
        sa.Column("xray_email", sa.String(length=255), nullable=False),
        sa.Column("xray_client_uuid", sa.String(length=64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_enabled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_disabled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("device_limit", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("xray_inbound_tag", "xray_email", name="uq_vpn_accesses_xray_identity"),
    )
    op.create_index(op.f("ix_vpn_accesses_expires_at"), "vpn_accesses", ["expires_at"], unique=False)
    op.create_index(op.f("ix_vpn_accesses_user_id"), "vpn_accesses", ["user_id"], unique=False)
    op.create_index(op.f("ix_vpn_accesses_xray_email"), "vpn_accesses", ["xray_email"], unique=False)
    op.create_unique_constraint("uq_vpn_accesses_xray_client_uuid", "vpn_accesses", ["xray_client_uuid"])

    op.create_table(
        "balance_transactions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("payment_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("type", sa.String(length=32), nullable=False),
        sa.Column("amount_kopecks", sa.Integer(), nullable=False),
        sa.Column("balance_after_kopecks", sa.Integer(), nullable=False),
        sa.Column("comment", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["payment_id"], ["payments.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_balance_transactions_payment_id"), "balance_transactions", ["payment_id"], unique=False)
    op.create_index(op.f("ix_balance_transactions_user_id"), "balance_transactions", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_balance_transactions_user_id"), table_name="balance_transactions")
    op.drop_index(op.f("ix_balance_transactions_payment_id"), table_name="balance_transactions")
    op.drop_table("balance_transactions")

    op.drop_constraint("uq_vpn_accesses_xray_client_uuid", "vpn_accesses", type_="unique")
    op.drop_index(op.f("ix_vpn_accesses_xray_email"), table_name="vpn_accesses")
    op.drop_index(op.f("ix_vpn_accesses_user_id"), table_name="vpn_accesses")
    op.drop_index(op.f("ix_vpn_accesses_expires_at"), table_name="vpn_accesses")
    op.drop_table("vpn_accesses")

    op.drop_constraint("uq_payments_telegram_payment_charge_id", "payments", type_="unique")
    op.drop_constraint("uq_payments_provider_payment_charge_id", "payments", type_="unique")
    op.drop_constraint("uq_payments_invoice_payload", "payments", type_="unique")
    op.drop_index(op.f("ix_payments_user_id"), table_name="payments")
    op.drop_table("payments")

    op.drop_index(op.f("ix_users_telegram_id"), table_name="users")
    op.drop_table("users")
