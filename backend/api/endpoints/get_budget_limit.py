from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.api.dependencies import current_user_resolver
from backend.database import get_db
from backend.models import UserBudgetLimit
from backend.schemas import BudgetLimitResponse


class GetBudgetLimitEndpoint:
    def register(self, router: APIRouter) -> None:
        router.add_api_route(
            "/budget/limit",
            self.handle,
            methods=["GET"],
            response_model=BudgetLimitResponse,
        )

    async def handle(
        self,
        user_id: str = Depends(current_user_resolver.resolve),
        db: Session = Depends(get_db),
    ) -> BudgetLimitResponse:
        setting = db.execute(
            select(UserBudgetLimit).where(UserBudgetLimit.user_id == user_id)
        ).scalar_one_or_none()
        if not setting:
            raise HTTPException(status_code=404, detail="Budget limit not set for this user.")
        return BudgetLimitResponse(monthly_budget=float(setting.monthly_budget), currency=setting.currency)
