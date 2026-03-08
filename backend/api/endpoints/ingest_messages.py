from __future__ import annotations

from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.api.dependencies import current_user_resolver
from backend.api.mappers import TransactionMapper
from backend.database import get_db
from backend.ingestion import IngestionInputRecord, ingest_messages
from backend.schemas import (
    IngestMessagesRequest,
    IngestMessagesResponse,
    IngestionItemResult,
)


class IngestMessagesEndpoint:
    def register(self, router: APIRouter) -> None:
        router.add_api_route(
            "/ingestion/messages",
            self.handle,
            methods=["POST"],
            response_model=IngestMessagesResponse,
        )

    async def handle(
        self,
        req: IngestMessagesRequest,
        user_id: str = Depends(current_user_resolver.resolve),
        db: Session = Depends(get_db),
    ) -> IngestMessagesResponse:
        batch_id = (req.batch_id or "").strip() or f"{req.mode}-{uuid4().hex[:12]}"
        records = [
            IngestionInputRecord(
                message=item.message,
                source_message_id=item.source_message_id,
                source_received_at=item.source_received_at,
                user_note=item.user_note,
                source=item.source,
            )
            for item in req.messages
        ]

        try:
            outcome = ingest_messages(
                db,
                user_id=user_id,
                mode=req.mode,
                records=records,
                batch_id=batch_id,
                default_source=req.source,
                default_user_note=req.user_note,
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e)) from e

        return IngestMessagesResponse(
            mode=req.mode,
            batch_id=batch_id,
            total=len(req.messages),
            stored=outcome.stored,
            duplicates=outcome.duplicates,
            failed=outcome.failed,
            results=[
                IngestionItemResult(
                    index=item.index,
                    status=item.status,
                    source_message_id=item.source_message_id,
                    error=item.error,
                    transaction=TransactionMapper.to_out(item.transaction) if item.transaction else None,
                )
                for item in outcome.results
            ],
        )
