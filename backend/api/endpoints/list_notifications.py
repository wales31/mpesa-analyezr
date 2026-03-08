from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.api.dependencies import current_user_resolver
from backend.api.mappers import NotificationMapper
from backend.database import get_db
from backend.models import Notification
from backend.schemas import NotificationsResponse


class ListNotificationsEndpoint:
    def register(self, router: APIRouter) -> None:
        router.add_api_route(
            "/notifications",
            self.handle,
            methods=["GET"],
            response_model=NotificationsResponse,
        )

    async def handle(
        self,
        limit: int = Query(default=50, ge=1, le=200),
        unread_only: bool = Query(default=False),
        user_id: str = Depends(current_user_resolver.resolve),
        db: Session = Depends(get_db),
    ) -> NotificationsResponse:
        stmt = select(Notification).where(Notification.user_id == user_id)
        if unread_only:
            stmt = stmt.where(Notification.is_read.is_(False))
        stmt = stmt.order_by(Notification.created_at.desc(), Notification.id.desc()).limit(limit)

        rows = db.execute(stmt).scalars().all()
        unread = db.execute(
            select(func.count(Notification.id)).where(
                Notification.user_id == user_id,
                Notification.is_read.is_(False),
            )
        ).scalar_one()

        return NotificationsResponse(
            count=len(rows),
            unread=int(unread),
            notifications=[NotificationMapper.to_out(item) for item in rows],
        )
