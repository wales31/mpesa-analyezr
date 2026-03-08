from __future__ import annotations

from fastapi import FastAPI

from backend.database import display_database_url, init_db


class StartupLifecycle:
    def register(self, app: FastAPI) -> None:
        @app.on_event("startup")
        async def startup() -> None:
            init_db()
            print(f"Database: {display_database_url()}")
