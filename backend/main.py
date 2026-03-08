from __future__ import annotations

from fastapi import FastAPI

from backend.api.app import MpesaAnalyzerApp


def create_app() -> FastAPI:
    return MpesaAnalyzerApp().build()


app = create_app()
 