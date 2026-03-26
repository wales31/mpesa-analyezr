from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import json
import re
from typing import Optional

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.categorizer import ClassificationInput, classify_transaction, serialize_breakdown
from backend.models import Transaction
from backend.notifications import generate_notifications
from backend.parser import ParseError, parse_mpesa_message

INGESTION_MODES = {"single_upload", "inbox_sync", "statement_import"}

_DEFAULT_SOURCE_BY_MODE = {
    "single_upload": "manual_upload",
    "inbox_sync": "android_inbox",
    "statement_import": "statement_upload",
}


@dataclass(frozen=True)
class IngestionInputRecord:
    message: str
    source_message_id: Optional[str] = None
    source_received_at: Optional[datetime] = None
    user_note: Optional[str] = None
    source: Optional[str] = None


@dataclass(frozen=True)
class IngestionResult:
    index: int
    status: str
    source_message_id: Optional[str]
    transaction: Optional[Transaction]
    error: Optional[str]


@dataclass(frozen=True)
class IngestionBatchResult:
    stored: int
    duplicates: int
    failed: int
    results: list[IngestionResult]


def ingest_messages(
    db: Session,
    *,
    user_id: str,
    mode: str,
    records: list[IngestionInputRecord],
    batch_id: Optional[str] = None,
    default_source: Optional[str] = None,
    default_user_note: Optional[str] = None,
) -> IngestionBatchResult:
    mode = (mode or "").strip().lower()
    if mode not in INGESTION_MODES:
        raise ValueError(f"Unsupported ingestion mode: {mode}")

    stored = 0
    duplicates = 0
    failed = 0
    results: list[IngestionResult] = []

    for index, record in enumerate(records):
        message = (record.message or "").strip()
        source_message_id = _clean_optional(record.source_message_id, max_len=128)
        source = _normalize_source(record.source or default_source, mode)
        user_note = _clean_optional(
            record.user_note if record.user_note is not None else default_user_note,
            max_len=500,
        )

        if not message:
            failed += 1
            results.append(
                IngestionResult(
                    index=index,
                    status="failed",
                    source_message_id=source_message_id,
                    transaction=None,
                    error="Message is empty.",
                )
            )
            continue

        try:
            parsed = parse_mpesa_message(message)
        except ParseError as e:
            failed += 1
            results.append(
                IngestionResult(
                    index=index,
                    status="failed",
                    source_message_id=source_message_id,
                    transaction=None,
                    error=str(e),
                )
            )
            continue

        existing = _find_existing_by_reference(db, user_id=user_id, reference=parsed.reference)
        if not existing and source_message_id:
            existing = _find_existing_by_source_message_id(
                db,
                user_id=user_id,
                mode=mode,
                source_message_id=source_message_id,
            )

        if existing:
            duplicates += 1
            results.append(
                IngestionResult(
                    index=index,
                    status="duplicate",
                    source_message_id=source_message_id,
                    transaction=existing,
                    error=None,
                )
            )
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
                user_note=user_note,
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
            user_note=user_note,
            user_correction_key=(
                f"merchant:{parsed.merchant_name.lower()}" if parsed.merchant_name else
                f"contact:{parsed.contact_name.lower()}" if parsed.contact_name else
                f"paybill:{parsed.paybill_number}" if parsed.paybill_number else
                f"till:{parsed.till_number}" if parsed.till_number else None
            ),
            source=source,
            ingestion_mode=mode,
            ingestion_batch_id=batch_id,
            source_message_id=source_message_id,
            source_received_at=record.source_received_at,
        )
        db.add(tx)

        try:
            db.commit()
        except IntegrityError:
            db.rollback()

            existing = _find_existing_by_reference(db, user_id=user_id, reference=parsed.reference)
            if not existing and source_message_id:
                existing = _find_existing_by_source_message_id(
                    db,
                    user_id=user_id,
                    mode=mode,
                    source_message_id=source_message_id,
                )

            if existing:
                duplicates += 1
                results.append(
                    IngestionResult(
                        index=index,
                        status="duplicate",
                        source_message_id=source_message_id,
                        transaction=existing,
                        error=None,
                    )
                )
                continue

            failed += 1
            results.append(
                IngestionResult(
                    index=index,
                    status="failed",
                    source_message_id=source_message_id,
                    transaction=None,
                    error="Duplicate or invalid transaction.",
                )
            )
            continue

        db.refresh(tx)
        stored += 1
        results.append(
            IngestionResult(
                index=index,
                status="stored",
                source_message_id=source_message_id,
                transaction=tx,
                error=None,
            )
        )

    if stored > 0:
        generate_notifications(db, user_id=user_id)

    return IngestionBatchResult(
        stored=stored,
        duplicates=duplicates,
        failed=failed,
        results=results,
    )


def _clean_optional(value: Optional[str], *, max_len: int) -> Optional[str]:
    cleaned = (value or "").strip()
    if not cleaned:
        return None
    return cleaned[:max_len]


def _normalize_source(value: Optional[str], mode: str) -> str:
    raw = (value or "").strip().lower()
    if not raw:
        return _DEFAULT_SOURCE_BY_MODE[mode]
    normalized = re.sub(r"[^a-z0-9_]+", "_", raw)
    normalized = re.sub(r"_+", "_", normalized).strip("_")
    if not normalized:
        return _DEFAULT_SOURCE_BY_MODE[mode]
    return normalized[:32]


def _find_existing_by_reference(db: Session, *, user_id: str, reference: Optional[str]) -> Optional[Transaction]:
    if not reference:
        return None
    return db.execute(
        select(Transaction).where(
            Transaction.user_id == user_id,
            Transaction.reference == reference,
        )
    ).scalar_one_or_none()


def _find_existing_by_source_message_id(
    db: Session,
    *,
    user_id: str,
    mode: str,
    source_message_id: str,
) -> Optional[Transaction]:
    return db.execute(
        select(Transaction).where(
            Transaction.user_id == user_id,
            Transaction.ingestion_mode == mode,
            Transaction.source_message_id == source_message_id,
        )
    ).scalar_one_or_none()
