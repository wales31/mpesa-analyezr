from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.api.dependencies import current_user_resolver
from backend.api.utils import DateTimeParser
from backend.database import get_db
from backend.models import Transaction
from backend.schemas import SummaryCategory, SummaryResponse


class SummaryEndpoint:
    def register(self, router: APIRouter) -> None:
        router.add_api_route("/summary", self.handle, methods=["GET"], response_model=SummaryResponse)

    async def handle(
        self,
        from_: Optional[str] = Query(default=None, alias="from"),
        to: Optional[str] = Query(default=None),
        user_id: str = Depends(current_user_resolver.resolve),
        db: Session = Depends(get_db),
    ) -> SummaryResponse:
        from_dt = DateTimeParser.parse_iso(from_) if from_ else None
        to_dt = DateTimeParser.parse_iso(to) if to else None

        total_stmt = select(func.coalesce(func.sum(Transaction.amount), 0)).where(
            Transaction.direction == "expense",
            Transaction.user_id == user_id,
        )
        if from_dt:
            total_stmt = total_stmt.where(Transaction.occurred_at >= from_dt)
        if to_dt:
            total_stmt = total_stmt.where(Transaction.occurred_at <= to_dt)
        total_spent = float(db.execute(total_stmt).scalar_one())

        cats_stmt = (
            select(Transaction.category, func.coalesce(func.sum(Transaction.amount), 0).label("amt"))
            .where(
                Transaction.direction == "expense",
                Transaction.user_id == user_id,
            )
            .group_by(Transaction.category)
            .order_by(func.sum(Transaction.amount).desc())
        )
        if from_dt:
            cats_stmt = cats_stmt.where(Transaction.occurred_at >= from_dt)
        if to_dt:
            cats_stmt = cats_stmt.where(Transaction.occurred_at <= to_dt)

        cats = [
            SummaryCategory(category=row[0], amount=float(row[1]))
            for row in db.execute(cats_stmt).all()
            if row[0] is not None
        ]
        return SummaryResponse(currency="KES", total_spent=total_spent, categories=cats)
