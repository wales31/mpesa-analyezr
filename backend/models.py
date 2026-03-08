from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("email", name="uq_users_email"),
        UniqueConstraint("username", name="uq_users_username"),
        Index("ix_users_email", "email"),
        Index("ix_users_username", "username"),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    username: Mapped[str] = mapped_column(String(64), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    tokens: Mapped[list["AuthToken"]] = relationship(
        "AuthToken",
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class AuthToken(Base):
    __tablename__ = "auth_tokens"
    __table_args__ = (
        UniqueConstraint("token_hash", name="uq_auth_tokens_hash"),
        Index("ix_auth_tokens_user_id", "user_id"),
        Index("ix_auth_tokens_expires_at", "expires_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    user: Mapped["User"] = relationship("User", back_populates="tokens")


class Transaction(Base):
    __tablename__ = "transactions"
    __table_args__ = (
        CheckConstraint(
            "direction IN ('income','expense','transfer')",
            name="ck_transactions_direction",
        ),
        UniqueConstraint("user_id", "reference", name="uq_transactions_user_reference"),
        Index("ix_transactions_user_id", "user_id"),
        Index("ix_transactions_occurred_at", "occurred_at"),
        Index("ix_transactions_category", "category"),
        Index("ix_transactions_direction", "direction"),
        Index("ix_transactions_source_message_id", "user_id", "source_message_id"),
        Index("ix_transactions_ingestion_mode", "ingestion_mode"),
        Index("ix_transactions_ingestion_batch_id", "ingestion_batch_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(8), nullable=False, default="KES")
    user_id: Mapped[str] = mapped_column(String(64), nullable=False, default="default")

    # direction is used for budgeting math (income vs expense vs transfer).
    direction: Mapped[str] = mapped_column(String(16), nullable=False, default="expense")

    category: Mapped[str] = mapped_column(String(64), nullable=False, default="uncategorized")

    # Raw-ish type from M-PESA context (e.g., sent, received, pay, paybill, withdraw, deposit).
    transaction_type: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)

    recipient: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    reference: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    occurred_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # User-provided context (what the money was for) to improve categorization.
    user_note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Ingestion metadata for Android sync/import workflows.
    ingestion_mode: Mapped[str] = mapped_column(String(32), nullable=False, default="single_upload")
    ingestion_batch_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    source_message_id: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    source_received_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    source: Mapped[str] = mapped_column(String(32), nullable=False, default="mpesa_sms")

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class CategoryLearningRule(Base):
    __tablename__ = "category_learning_rules"
    __table_args__ = (
        UniqueConstraint("user_id", "match_key", name="uq_category_learning_rules_user_match"),
        Index("ix_category_learning_rules_user_id", "user_id"),
        Index("ix_category_learning_rules_match_key", "match_key"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(64), nullable=False)
    match_key: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(64), nullable=False)
    learned_from_tx_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    usage_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)


class UserBudgetLimit(Base):
    __tablename__ = "user_budget_limits"
    __table_args__ = (
        UniqueConstraint("user_id", name="uq_user_budget_limits_user"),
        Index("ix_user_budget_limits_user_id", "user_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(64), nullable=False)
    currency: Mapped[str] = mapped_column(String(8), nullable=False, default="KES")
    monthly_budget: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)


class Notification(Base):
    __tablename__ = "notifications"
    __table_args__ = (
        UniqueConstraint("user_id", "dedupe_key", name="uq_notifications_user_dedupe"),
        Index("ix_notifications_user_id", "user_id"),
        Index("ix_notifications_created_at", "created_at"),
        Index("ix_notifications_read", "is_read"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(64), nullable=False)
    kind: Mapped[str] = mapped_column(String(32), nullable=False, default="spending_insight")
    severity: Mapped[str] = mapped_column(String(16), nullable=False, default="info")
    title: Mapped[str] = mapped_column(String(128), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    dedupe_key: Mapped[str] = mapped_column(String(255), nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)


class Budget(Base):
    __tablename__ = "budgets"
    __table_args__ = (
        UniqueConstraint("period_start", "period_end", name="uq_budgets_period"),
        Index("ix_budgets_period_start", "period_start"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Period boundaries. For monthly budgets, start = first day, end = first day of next month.
    period_start: Mapped[date] = mapped_column(Date, nullable=False)
    period_end: Mapped[date] = mapped_column(Date, nullable=False)

    currency: Mapped[str] = mapped_column(String(8), nullable=False, default="KES")
    planned_income: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    lines: Mapped[list["BudgetLine"]] = relationship(
        "BudgetLine",
        back_populates="budget",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class BudgetLine(Base):
    __tablename__ = "budget_lines"
    __table_args__ = (
        CheckConstraint(
            "direction IN ('income','expense')",
            name="ck_budget_lines_direction",
        ),
        UniqueConstraint("budget_id", "direction", "category", name="uq_budget_lines_budget_dir_cat"),
        Index("ix_budget_lines_budget_id", "budget_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    budget_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("budgets.id", ondelete="CASCADE"), nullable=False
    )
    budget: Mapped["Budget"] = relationship("Budget", back_populates="lines")

    direction: Mapped[str] = mapped_column(String(16), nullable=False, default="expense")
    category: Mapped[str] = mapped_column(String(64), nullable=False)
    planned_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
