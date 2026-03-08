from __future__ import annotations

from fastapi import APIRouter

from backend.api.endpoints import (
    AuthEndpoint,
    AnalyzeBulkEndpoint,
    AnalyzeEndpoint,
    CategorizeTransactionEndpoint,
    ClearTransactionsEndpoint,
    GetBudgetLimitEndpoint,
    HealthEndpoint,
    IngestMessagesEndpoint,
    InsightsEndpoint,
    ListNotificationsEndpoint,
    ListTransactionsEndpoint,
    MarkAllNotificationsReadEndpoint,
    MarkNotificationReadEndpoint,
    RefreshNotificationsEndpoint,
    SummaryEndpoint,
    UpsertBudgetLimitEndpoint,
)


class ApiRouterRegistry:
    def __init__(self) -> None:
        self._endpoints = [
            HealthEndpoint(),
            AuthEndpoint(),
            AnalyzeEndpoint(),
            AnalyzeBulkEndpoint(),
            IngestMessagesEndpoint(),
            ListTransactionsEndpoint(),
            CategorizeTransactionEndpoint(),
            ClearTransactionsEndpoint(),
            SummaryEndpoint(),
            InsightsEndpoint(),
            UpsertBudgetLimitEndpoint(),
            GetBudgetLimitEndpoint(),
            RefreshNotificationsEndpoint(),
            ListNotificationsEndpoint(),
            MarkNotificationReadEndpoint(),
            MarkAllNotificationsReadEndpoint(),
        ]

    def build(self) -> APIRouter:
        router = APIRouter()
        for endpoint in self._endpoints:
            endpoint.register(router)
        return router
