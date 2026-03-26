from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.api.dependencies import current_user_resolver
from backend.api.mappers import TransactionMapper
from backend.categorizer import ClassificationInput, classify_transaction, serialize_breakdown
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

            classification = classify_transaction(
                db,
                user_id=user_id,
                data=ClassificationInput(
                    message=parsed.raw_message,
                    normalized_message=parsed.normalized_message,
                    recipient=parsed.recipient,
                    merchant_name=parsed.merchant_name,
                    contact_name=parsed.contact_name,
                    paybill_number=parsed.paybill_number,
                    till_number=parsed.till_number,
                    account_reference=parsed.account_reference,
                    transaction_code=parsed.transaction_code,
                    canonical_entity_name=parsed.canonical_entity_name,
                    normalized_text_signature=parsed.normalized_text_signature,
                    parsed_direction=parsed.direction,
                    parsed_sub_type=parsed.transaction_type,
                    user_note=req.user_note,
                ),
            )
            tx = Transaction(
                user_id=user_id,
                amount=parsed.amount,
                currency=parsed.currency,
                direction=classification.transaction_type,
                transaction_type=classification.transaction_type,
                transaction_sub_type=classification.transaction_sub_type,
                recipient=parsed.recipient,
                merchant_name=parsed.merchant_name,
                contact_name=parsed.contact_name,
                paybill_number=parsed.paybill_number,
                till_number=parsed.till_number,
                account_reference=parsed.account_reference,
                reference=parsed.reference,
                occurred_at=parsed.occurred_at,
                raw_message=parsed.raw_message,
                normalized_message=parsed.normalized_message,
                category=classification.category,
                confidence_score=classification.confidence_score,
                classification_source=classification.classification_source,
                matched_rule=classification.matched_rule,
                matched_priority_tier=classification.matched_priority_tier,
                matched_key_type=classification.matched_key_type,
                canonical_entity_name=parsed.canonical_entity_name,
                normalized_text_signature=parsed.normalized_text_signature,
                confidence_band=classification.confidence_band,
                confidence_breakdown=serialize_breakdown(classification.confidence_breakdown),
                confidence_reason_summary=classification.confidence_reason_summary,
                conflict_flag=classification.conflict_flag,
                conflict_reasons=json.dumps(classification.conflict_reasons),
                competing_rules=json.dumps(classification.competing_rules),
                needs_review=classification.needs_review,
                category_suggestions="|".join(classification.suggestions),
                user_note=req.user_note,
                user_correction_key=(
                    f"merchant:{parsed.merchant_name.lower()}" if parsed.merchant_name else
                    f"contact:{parsed.contact_name.lower()}" if parsed.contact_name else
                    f"paybill:{parsed.paybill_number}" if parsed.paybill_number else
                    f"till:{parsed.till_number}" if parsed.till_number else None
                ),
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
