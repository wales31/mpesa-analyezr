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
from backend.schemas import AnalyzeBulkRequest, AnalyzeBulkResponse, TransactionOut


class AnalyzeBulkEndpoint:
    def register(self, router: APIRouter) -> None:
        router.add_api_route(
            "/analyze/bulk",
            self.handle,
            methods=["POST"],
            response_model=AnalyzeBulkResponse,
        )

    async def handle(
        self,
        req: AnalyzeBulkRequest,
        user_id: str = Depends(current_user_resolver.resolve),
        db: Session = Depends(get_db),
    ) -> AnalyzeBulkResponse:
        stored = 0
        failed = 0
        out: list[TransactionOut] = []

        for msg in req.messages:
            msg = (msg or "").strip()
            if not msg:
                continue

            try:
                parsed = parse_mpesa_message(msg)
            except ParseError:
                failed += 1
                continue

            if parsed.reference:
                existing = db.execute(
                    select(Transaction).where(
                        Transaction.user_id == user_id,
                        Transaction.reference == parsed.reference,
                    )
                ).scalar_one_or_none()
                if existing:
                    out.append(TransactionMapper.to_out(existing))
                    continue

            category = categorize_hybrid(
                db,
                user_id=user_id,
                message=msg,
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
            except IntegrityError:
                db.rollback()
                failed += 1
                continue

            db.refresh(tx)
            stored += 1
            out.append(TransactionMapper.to_out(tx))

        if stored == 0 and not out:
            raise HTTPException(status_code=400, detail="No valid messages provided.")

        if stored > 0:
            generate_notifications(db, user_id=user_id)

        return AnalyzeBulkResponse(stored=stored, failed=failed, transactions=out)
