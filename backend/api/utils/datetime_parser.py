from __future__ import annotations

from datetime import datetime
from typing import Optional


class DateTimeParser:
    @staticmethod
    def parse_iso(value: str) -> Optional[datetime]:
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            return None
