from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.api.dependencies import current_user_resolver
from backend.api.mappers import NotificationMapper
from backend.database import get_db
from backend.models import Notification
from backend.schemas import NotificationOut, NotificationReadRequest


class MarkNotificationReadEndpoint:
    def register(self, router: APIRouter) -> None:
        router.add_api_route(
            "/notifications/{notification_id}/read",
            self.handle,
            methods=["PATCH"],
            response_model=NotificationOut,
        )

    async def handle(
        self,
        notification_id: int,
        req: NotificationReadRequest,
        user_id: str = Depends(current_user_resolver.resolve),
        db: Session = Depends(get_db),
    ) -> NotificationOut:
        item = db.execute(
            select(Notification).where(
                Notification.id == notification_id,
                Notification.user_id == user_id,
            )
        ).scalar_one_or_none()
        if not item:
            raise HTTPException(status_code=404, detail="Notification not found.")

        item.is_read = bool(req.is_read)
        item.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(item)
        return NotificationMapper.to_out(item)
