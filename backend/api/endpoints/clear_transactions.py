from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import delete
from sqlalchemy.orm import Session

from backend.api.dependencies import current_user_resolver
from backend.database import get_db
from backend.models import Notification, Transaction
from backend.schemas import MessageResponse


class ClearTransactionsEndpoint:
    def register(self, router: APIRouter) -> None:
        router.add_api_route(
            "/transactions",
            self.handle,
            methods=["DELETE"],
            response_model=MessageResponse,
        )

    async def handle(
        self,
        user_id: str = Depends(current_user_resolver.resolve),
        db: Session = Depends(get_db),
    ) -> MessageResponse:
        db.execute(delete(Transaction).where(Transaction.user_id == user_id))
        db.execute(delete(Notification).where(Notification.user_id == user_id))
        db.commit()
        return MessageResponse(message="User transactions deleted.")
