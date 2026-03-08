from __future__ import annotations

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.router import ApiRouterRegistry
from backend.api.startup import StartupLifecycle


class MpesaAnalyzerApp:
    def __init__(self) -> None:
        self._app = FastAPI(title="M-PESA Analyzer API", version="0.2.0")
        self._router_registry = ApiRouterRegistry()
        self._startup_lifecycle = StartupLifecycle()

    def build(self) -> FastAPI:
        self._configure_middleware()
        self._configure_routes()
        self._startup_lifecycle.register(self._app)
        return self._app

    def _configure_middleware(self) -> None:
        origins = self._resolve_cors_origins()
        allow_all = "*" in origins
        self._app.add_middleware(
            CORSMiddleware,
            allow_origins=origins,
            allow_origin_regex=None if allow_all else self._resolve_cors_origin_regex(),
            allow_credentials=not allow_all,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    def _configure_routes(self) -> None:
        self._app.include_router(self._router_registry.build())

    def _resolve_cors_origins(self) -> list[str]:
        raw = (
            os.getenv("MPESA_CORS_ORIGINS")
            or "http://127.0.0.1:5173,http://localhost:5173,http://127.0.0.1:8000,http://localhost:8000"
        ).strip()
        if raw == "*":
            return ["*"]
        origins = [item.strip().rstrip("/") for item in raw.split(",") if item.strip()]
        return origins or ["http://127.0.0.1:5173", "http://localhost:5173"]

    def _resolve_cors_origin_regex(self) -> str | None:
        raw = os.getenv("MPESA_CORS_ORIGIN_REGEX")
        if raw is not None:
            value = raw.strip()
            return value or None

        # Default local-development support for browsers opened via LAN IPs.
        if os.getenv("MPESA_CORS_ORIGINS"):
            return None

        return (
            r"^https?://("
            r"localhost|127(?:\.\d{1,3}){3}|0\.0\.0\.0|\[::1\]|"
            r"10(?:\.\d{1,3}){3}|"
            r"192\.168(?:\.\d{1,3}){2}|"
            r"172\.(?:1[6-9]|2\d|3[0-1])(?:\.\d{1,3}){2}"
            r")(?::\d+)?$"
        )
