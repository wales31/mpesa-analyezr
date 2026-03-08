from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from hashlib import sha1
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.insights import build_insights
from backend.models import Notification, Transaction, UserBudgetLimit


def _to_float(value: Optional[Decimal]) -> float:
    if value is None:
        return 0.0
    return float(value)


def _month_range(reference: datetime) -> tuple[datetime, datetime, str]:
    month_start = reference.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    if month_start.month == 12:
        next_month = month_start.replace(year=month_start.year + 1, month=1)
    else:
        next_month = month_start.replace(month=month_start.month + 1)
    month_key = month_start.strftime("%Y-%m")
    return month_start, next_month, month_key


def _upsert_notification(
    db: Session,
    *,
    user_id: str,
    kind: str,
    severity: str,
    title: str,
    message: str,
    dedupe_key: str,
) -> bool:
    existing = db.execute(
        select(Notification).where(
            Notification.user_id == user_id,
            Notification.dedupe_key == dedupe_key,
        )
    ).scalar_one_or_none()
    now = datetime.utcnow()
    if existing:
        # If message changes, surface it again as unread.
        if existing.message != message or existing.severity != severity:
            existing.title = title
            existing.message = message
            existing.severity = severity
            existing.is_read = False
            existing.updated_at = now
        return False

    db.add(
        Notification(
            user_id=user_id,
            kind=kind,
            severity=severity,
            title=title,
            message=message,
            dedupe_key=dedupe_key,
            is_read=False,
            updated_at=now,
        )
    )
    return True


def generate_notifications(db: Session, *, user_id: str) -> tuple[int, int]:
    """
    Generate in-app notifications for a user from:
    - budget usage thresholds
    - spending insights
    Returns (created_count, total_notification_count_for_user).
    """
    created = 0
    now = datetime.utcnow()
    month_start, next_month, month_key = _month_range(now)

    budget_limit = db.execute(
        select(UserBudgetLimit).where(UserBudgetLimit.user_id == user_id)
    ).scalar_one_or_none()

    if budget_limit and float(budget_limit.monthly_budget) > 0:
        spent_stmt = (
            select(func.coalesce(func.sum(Transaction.amount), 0))
            .where(
                Transaction.user_id == user_id,
                Transaction.direction == "expense",
                Transaction.occurred_at >= month_start,
                Transaction.occurred_at < next_month,
            )
        )
        spent = _to_float(db.execute(spent_stmt).scalar_one())
        budget = _to_float(budget_limit.monthly_budget)
        usage = spent / budget if budget > 0 else 0.0

        if usage >= 1.0:
            created += int(
                _upsert_notification(
                    db,
                    user_id=user_id,
                    kind="budget_alert",
                    severity="warning",
                    title="Monthly budget exceeded",
                    message=(
                        f"You have spent {spent:.2f} {budget_limit.currency} "
                        f"against a budget of {budget:.2f} {budget_limit.currency} for {month_key}."
                    ),
                    dedupe_key=f"budget_exceeded:{month_key}",
                )
            )
        elif usage >= 0.8:
            created += int(
                _upsert_notification(
                    db,
                    user_id=user_id,
                    kind="budget_alert",
                    severity="info",
                    title="Budget nearing limit",
                    message=(
                        f"You have used {usage * 100:.0f}% of your {month_key} budget "
                        f"({spent:.2f}/{budget:.2f} {budget_limit.currency})."
                    ),
                    dedupe_key=f"budget_nearing:{month_key}",
                )
            )

    warnings, highlights = build_insights(db, user_id=user_id)
    for warning in warnings:
        key = f"insight_warning:{sha1(warning.encode('utf-8')).hexdigest()[:24]}"
        created += int(
            _upsert_notification(
                db,
                user_id=user_id,
                kind="spending_insight",
                severity="warning",
                title="Spending warning",
                message=warning,
                dedupe_key=key,
            )
        )
    for highlight in highlights:
        key = f"insight_highlight:{sha1(highlight.encode('utf-8')).hexdigest()[:24]}"
        created += int(
            _upsert_notification(
                db,
                user_id=user_id,
                kind="spending_insight",
                severity="info",
                title="Spending insight",
                message=highlight,
                dedupe_key=key,
            )
        )

    db.commit()
    total = db.execute(
        select(func.count(Notification.id)).where(Notification.user_id == user_id)
    ).scalar_one()
    return created, int(total)
