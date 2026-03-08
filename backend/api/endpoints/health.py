from __future__ import annotations

from fastapi import APIRouter

from backend.schemas import MessageResponse


class HealthEndpoint:
    def register(self, router: APIRouter) -> None:
        router.add_api_route("/", self.handle, methods=["GET"], response_model=MessageResponse)

    async def handle(self) -> MessageResponse:
        return MessageResponse(message="M-PESA Analyzer API Running")
