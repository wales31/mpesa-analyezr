from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.api.dependencies import current_user_resolver
from backend.database import get_db
from backend.models import UserBudgetLimit
from backend.notifications import generate_notifications
from backend.schemas import BudgetLimitResponse, BudgetLimitUpsertRequest


class UpsertBudgetLimitEndpoint:
    def register(self, router: APIRouter) -> None:
        router.add_api_route(
            "/budget/limit",
            self.handle,
            methods=["PUT"],
            response_model=BudgetLimitResponse,
        )

    async def handle(
        self,
        req: BudgetLimitUpsertRequest,
        user_id: str = Depends(current_user_resolver.resolve),
        db: Session = Depends(get_db),
    ) -> BudgetLimitResponse:
        setting = db.execute(
            select(UserBudgetLimit).where(UserBudgetLimit.user_id == user_id)
        ).scalar_one_or_none()
        budget = Decimal(str(req.monthly_budget))
        currency = req.currency.upper().strip()

        if setting:
            setting.monthly_budget = budget
            setting.currency = currency
            setting.updated_at = datetime.utcnow()
        else:
            setting = UserBudgetLimit(
                user_id=user_id,
                monthly_budget=budget,
                currency=currency,
                updated_at=datetime.utcnow(),
            )
            db.add(setting)

        db.commit()
        db.refresh(setting)
        generate_notifications(db, user_id=user_id)
        return BudgetLimitResponse(monthly_budget=float(setting.monthly_budget), currency=setting.currency)
