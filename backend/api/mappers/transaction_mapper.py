from __future__ import annotations

import json

from backend.models import Transaction
from backend.schemas import TransactionOut


class TransactionMapper:
    @staticmethod
    def _safe_json_load(value: str | None, default):
        if not value:
            return default
        try:
            return json.loads(value)
        except (TypeError, json.JSONDecodeError):
            return default

    @staticmethod
    def to_out(tx: Transaction) -> TransactionOut:
        occurred_at = tx.occurred_at
        date = occurred_at.date().isoformat() if occurred_at else None
        time = occurred_at.time().isoformat(timespec="minutes") if occurred_at else None
        return TransactionOut(
            id=tx.id,
            amount=float(tx.amount),
            currency=tx.currency,
            category=tx.category,
            direction=tx.direction,
            transaction_type=tx.transaction_type,
            transaction_sub_type=tx.transaction_sub_type,
            recipient=tx.recipient,
            merchant_name=tx.merchant_name,
            contact_name=tx.contact_name,
            paybill_number=tx.paybill_number,
            till_number=tx.till_number,
            account_reference=tx.account_reference,
            raw_message=tx.raw_message,
            normalized_message=tx.normalized_message,
            confidence_score=float(tx.confidence_score) if tx.confidence_score is not None else None,
            classification_source=tx.classification_source,
            matched_rule=tx.matched_rule,
            matched_priority_tier=tx.matched_priority_tier,
            matched_key_type=tx.matched_key_type,
            correction_scope=tx.correction_scope,
            correction_match_basis=tx.correction_match_basis,
            canonical_entity_name=tx.canonical_entity_name,
            normalized_text_signature=tx.normalized_text_signature,
            confidence_band=tx.confidence_band,
            confidence_breakdown=TransactionMapper._safe_json_load(tx.confidence_breakdown, None),
            confidence_reason_summary=tx.confidence_reason_summary,
            conflict_flag=tx.conflict_flag,
            conflict_reasons=TransactionMapper._safe_json_load(tx.conflict_reasons, []),
            competing_rules=TransactionMapper._safe_json_load(tx.competing_rules, []),
            needs_review=tx.needs_review,
            category_suggestions=[s for s in (tx.category_suggestions or "").split("|") if s],
            user_corrected_category=tx.user_corrected_category,
            user_correction_key=tx.user_correction_key,
            reference=tx.reference,
            occurred_at=occurred_at,
            date=date,
            time=time,
            user_note=tx.user_note,
            ingestion_mode=tx.ingestion_mode,
            ingestion_batch_id=tx.ingestion_batch_id,
            source_message_id=tx.source_message_id,
            source_received_at=tx.source_received_at,
            source=tx.source,
        )
