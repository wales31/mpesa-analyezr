from __future__ import annotations

import json

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
        tx.user_corrected_category = category
        tx.classification_source = "manual"

        scope = req.correction_scope or tx.correction_scope or "merchant_plus_account"

        keys = remember_manual_category(
            db,
            user_id=user_id,
            category=category,
            merchant_name=tx.merchant_name,
            contact_name=tx.contact_name,
            recipient=tx.recipient,
            paybill_number=tx.paybill_number,
            till_number=tx.till_number,
            account_reference=tx.account_reference,
            normalized_message=tx.normalized_message,
            transaction_code=tx.reference,
            correction_scope=scope,
            correction_match_basis="manual_correction",
            canonical_entity_name_value=tx.canonical_entity_name,
            normalized_text_signature_value=tx.normalized_text_signature,
            broad_apply=req.broad_apply,
            learned_from_tx_id=tx.id,
        )
        correction_key = keys[0] if keys else None
        tx.user_correction_key = correction_key
        tx.correction_scope = scope
        tx.correction_match_basis = "manual_correction"
        tx.needs_review = False
        tx.conflict_flag = False
        tx.conflict_reasons = json.dumps([])
        tx.competing_rules = json.dumps([])

        if req.apply_to_similar and correction_key:
            similar = db.execute(
                select(Transaction).where(
                    Transaction.user_id == user_id,
                    Transaction.user_correction_key == correction_key,
                    Transaction.id != tx.id,
                )
            ).scalars().all()
            for item in similar:
                item.category = category
                item.classification_source = "learned_rule"
                item.user_corrected_category = category
                item.correction_scope = scope
                item.correction_match_basis = "manual_apply_to_similar"

        db.commit()
        db.refresh(tx)
        generate_notifications(db, user_id=user_id)
        return TransactionMapper.to_out(tx)
