from __future__ import annotations

from datetime import datetime

from backend.models import Notification
from backend.schemas import NotificationOut


class NotificationMapper:
    @staticmethod
    def to_out(item: Notification) -> NotificationOut:
        created_at = item.created_at or datetime.utcnow()
        return NotificationOut(
            id=item.id,
            kind=item.kind,
            severity=item.severity,
            title=item.title,
            message=item.message,
            is_read=bool(item.is_read),
            created_at=created_at,
        )
