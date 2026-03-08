from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.api.dependencies import current_user_resolver
from backend.database import get_db
from backend.notifications import generate_notifications
from backend.schemas import NotificationRefreshResponse


class RefreshNotificationsEndpoint:
    def register(self, router: APIRouter) -> None:
        router.add_api_route(
            "/notifications/refresh",
            self.handle,
            methods=["POST"],
            response_model=NotificationRefreshResponse,
        )

    async def handle(
        self,
        user_id: str = Depends(current_user_resolver.resolve),
        db: Session = Depends(get_db),
    ) -> NotificationRefreshResponse:
        created, total = generate_notifications(db, user_id=user_id)
        return NotificationRefreshResponse(created=created, total=total)
