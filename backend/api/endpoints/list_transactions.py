from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.api.dependencies import current_user_resolver
from backend.api.mappers import TransactionMapper
from backend.api.utils import DateTimeParser
from backend.categorizer import normalize_category
from backend.database import get_db
from backend.models import Transaction
from backend.schemas import TransactionsResponse


class ListTransactionsEndpoint:
    def register(self, router: APIRouter) -> None:
        router.add_api_route(
            "/transactions",
            self.handle,
            methods=["GET"],
            response_model=TransactionsResponse,
        )

    async def handle(
        self,
        limit: int = Query(default=50, ge=1, le=200),
        category: Optional[str] = Query(default=None),
        type_: Optional[str] = Query(default=None, alias="type"),
        from_: Optional[str] = Query(default=None, alias="from"),
        to: Optional[str] = Query(default=None),
        user_id: str = Depends(current_user_resolver.resolve),
        db: Session = Depends(get_db),
    ) -> TransactionsResponse:
        stmt = select(Transaction).where(Transaction.user_id == user_id)

        if category:
            stmt = stmt.where(Transaction.category == normalize_category(category))
        if type_:
            stmt = stmt.where(Transaction.transaction_type == type_)

        from_dt = DateTimeParser.parse_iso(from_) if from_ else None
        to_dt = DateTimeParser.parse_iso(to) if to else None
        if from_dt:
            stmt = stmt.where(Transaction.occurred_at >= from_dt)
        if to_dt:
            stmt = stmt.where(Transaction.occurred_at <= to_dt)

        stmt = stmt.order_by(Transaction.occurred_at.desc(), Transaction.id.desc()).limit(limit)
        rows = db.execute(stmt).scalars().all()
        return TransactionsResponse(
            count=len(rows),
            transactions=[TransactionMapper.to_out(tx) for tx in rows],
        )
