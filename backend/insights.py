from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.models import Transaction


def _safe_float(value: Optional[Decimal]) -> float:
    if value is None:
        return 0.0
    return float(value)


def build_insights(db: Session, user_id: Optional[str] = None) -> tuple[list[str], list[str]]:
    """
    Generate lightweight insights from stored transactions (v1).

    Notes:
    - Only considers expenses for spending insights.
    - Keeps rules intentionally simple and explainable.
    """

    warnings: list[str] = []
    highlights: list[str] = []
    expense_filters = [Transaction.direction == "expense"]
    if user_id:
        expense_filters.append(Transaction.user_id == user_id)

    # Total expense amount
    total_stmt = select(func.coalesce(func.sum(Transaction.amount), 0)).where(*expense_filters)
    total_spent = _safe_float(db.execute(total_stmt).scalar_one())

    # Top expense category
    top_stmt = (
        select(Transaction.category, func.coalesce(func.sum(Transaction.amount), 0).label("amt"))
        .where(*expense_filters)
        .group_by(Transaction.category)
        .order_by(func.sum(Transaction.amount).desc())
        .limit(1)
    )
    top_row = db.execute(top_stmt).first()
    if top_row and top_row[0]:
        highlights.append(f"Top spending category: {top_row[0]}")

    # Average daily spending based on occurred_at span
    min_dt: Optional[datetime] = db.execute(select(func.min(Transaction.occurred_at)).where(*expense_filters)).scalar_one()
    max_dt: Optional[datetime] = db.execute(select(func.max(Transaction.occurred_at)).where(*expense_filters)).scalar_one()
    if min_dt and max_dt:
        days = max(1, (max_dt.date() - min_dt.date()).days + 1)
        highlights.append(f"Average daily spending: {total_spent / days:.2f}")

    # Simple category warnings
    betting_stmt = (
        select(func.coalesce(func.sum(Transaction.amount), 0))
        .where(*expense_filters, Transaction.category == "betting")
    )
    betting_spent = _safe_float(db.execute(betting_stmt).scalar_one())
    if betting_spent > 0 and total_spent > 0 and (betting_spent / total_spent) >= 0.25:
        warnings.append("High spending detected in betting category.")

    # Frequency warning (many small transfers/expenses)
    small_tx_count = db.execute(
        select(func.count(Transaction.id)).where(
            *expense_filters,
            Transaction.amount <= 100,
        )
    ).scalar_one()
    if small_tx_count >= 20:
        warnings.append("Frequent small transfers detected.")

    return warnings, highlights
