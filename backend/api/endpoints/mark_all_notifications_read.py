from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy import update
from sqlalchemy.orm import Session

from backend.api.dependencies import current_user_resolver
from backend.database import get_db
from backend.models import Notification
from backend.schemas import MessageResponse


class MarkAllNotificationsReadEndpoint:
    def register(self, router: APIRouter) -> None:
        router.add_api_route(
            "/notifications/read-all",
            self.handle,
            methods=["POST"],
            response_model=MessageResponse,
        )

    async def handle(
        self,
        user_id: str = Depends(current_user_resolver.resolve),
        db: Session = Depends(get_db),
    ) -> MessageResponse:
        db.execute(
            update(Notification)
            .where(Notification.user_id == user_id, Notification.is_read.is_(False))
            .values(is_read=True, updated_at=datetime.utcnow())
        )
        db.commit()
        return MessageResponse(message="All notifications marked as read.")
