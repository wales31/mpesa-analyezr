from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.api.dependencies import current_user_resolver
from backend.api.mappers import TransactionMapper
from backend.categorizer import categorize_hybrid
from backend.database import get_db
from backend.models import Transaction
from backend.notifications import generate_notifications
from backend.parser import ParseError, parse_mpesa_message
from backend.schemas import AnalyzeRequest, AnalyzeResponse


class AnalyzeEndpoint:
    def register(self, router: APIRouter) -> None:
        router.add_api_route("/analyze", self.handle, methods=["POST"], response_model=AnalyzeResponse)

    async def handle(
        self,
        req: AnalyzeRequest,
        user_id: str = Depends(current_user_resolver.resolve),
        db: Session = Depends(get_db),
    ) -> AnalyzeResponse:
        try:
            parsed = parse_mpesa_message(req.message)
        except ParseError as e:
            raise HTTPException(status_code=400, detail=str(e)) from e

        if parsed.reference:
            existing = db.execute(
                select(Transaction).where(
                    Transaction.user_id == user_id,
                    Transaction.reference == parsed.reference,
                )
            ).scalar_one_or_none()
            if existing:
                return AnalyzeResponse(stored=False, transaction=TransactionMapper.to_out(existing))

        category = categorize_hybrid(
            db,
            user_id=user_id,
            message=req.message,
            user_note=req.user_note,
            recipient=parsed.recipient,
            transaction_type=parsed.transaction_type,
        )
        tx = Transaction(
            user_id=user_id,
            amount=parsed.amount,
            currency=parsed.currency,
            direction=parsed.direction,
            transaction_type=parsed.transaction_type,
            recipient=parsed.recipient,
            reference=parsed.reference,
            occurred_at=parsed.occurred_at,
            category=category,
            user_note=req.user_note,
            source="manual_upload",
            ingestion_mode="single_upload",
        )
        db.add(tx)

        try:
            db.commit()
        except IntegrityError as e:
            db.rollback()
            if parsed.reference:
                existing = db.execute(
                    select(Transaction).where(
                        Transaction.user_id == user_id,
                        Transaction.reference == parsed.reference,
                    )
                ).scalar_one_or_none()
                if existing:
                    return AnalyzeResponse(stored=False, transaction=TransactionMapper.to_out(existing))
            raise HTTPException(status_code=400, detail="Duplicate or invalid transaction.") from e

        db.refresh(tx)
        generate_notifications(db, user_id=user_id)
        return AnalyzeResponse(stored=True, transaction=TransactionMapper.to_out(tx))
