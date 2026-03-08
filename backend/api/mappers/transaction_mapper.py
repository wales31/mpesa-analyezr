from __future__ import annotations

from backend.models import Transaction
from backend.schemas import TransactionOut


class TransactionMapper:
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
            recipient=tx.recipient,
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
