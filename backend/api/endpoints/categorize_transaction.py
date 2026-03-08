from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.api.dependencies import current_user_resolver
from backend.api.mappers import TransactionMapper
from backend.categorizer import normalize_category, remember_manual_category
from backend.database import get_db
from backend.models import Transaction
from backend.notifications import generate_notifications
from backend.schemas import TransactionOut, UpdateCategoryRequest


class CategorizeTransactionEndpoint:
    def register(self, router: APIRouter) -> None:
        router.add_api_route(
            "/transactions/{transaction_id}/category",
            self.handle,
            methods=["PUT"],
            response_model=TransactionOut,
        )

    async def handle(
        self,
        transaction_id: int,
        req: UpdateCategoryRequest,
        user_id: str = Depends(current_user_resolver.resolve),
        db: Session = Depends(get_db),
    ) -> TransactionOut:
        tx = db.execute(
            select(Transaction).where(
                Transaction.id == transaction_id,
                Transaction.user_id == user_id,
            )
        ).scalar_one_or_none()
        if not tx:
            raise HTTPException(status_code=404, detail="Transaction not found.")

        category = normalize_category(req.category)
        tx.category = category
        tx.user_id = user_id

        remember_manual_category(
            db,
            user_id=user_id,
            category=category,
            message=None,
            user_note=tx.user_note,
            recipient=tx.recipient,
            transaction_type=tx.transaction_type,
            learned_from_tx_id=tx.id,
        )

        db.commit()
        db.refresh(tx)
        generate_notifications(db, user_id=user_id)
        return TransactionMapper.to_out(tx)
