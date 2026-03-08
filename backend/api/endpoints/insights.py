from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.api.dependencies import current_user_resolver
from backend.database import get_db
from backend.insights import build_insights
from backend.schemas import InsightsResponse


class InsightsEndpoint:
    def register(self, router: APIRouter) -> None:
        router.add_api_route("/insights", self.handle, methods=["GET"], response_model=InsightsResponse)

    async def handle(
        self,
        user_id: str = Depends(current_user_resolver.resolve),
        db: Session = Depends(get_db),
    ) -> InsightsResponse:
        warnings, highlights = build_insights(db, user_id=user_id)
        return InsightsResponse(warnings=warnings, highlights=highlights)
