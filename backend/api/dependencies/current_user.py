from __future__ import annotations

import os
import re
from datetime import datetime, timezone
from typing import Optional

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import AuthToken, User
from backend.security import hash_token


class CurrentUserResolver:
    _legacy_pattern = re.compile(r"^[A-Za-z0-9_.:@-]{1,64}$")

    def __init__(self) -> None:
        raw = (os.getenv("MPESA_ALLOW_LEGACY_USER_HEADER") or "").strip().lower()
        self._allow_legacy_user_header = raw in {"1", "true", "yes", "on"}

    def resolve(
        self,
        authorization: Optional[str] = Header(default=None, alias="Authorization"),
        x_user_id: Optional[str] = Header(default=None, alias="X-User-ID"),
        db: Session = Depends(get_db),
    ) -> str:
        token = self._extract_bearer_token(authorization)
        if token:
            now = datetime.now(timezone.utc)
            token_row = db.execute(
                select(AuthToken.user_id)
                .join(User, User.id == AuthToken.user_id)
                .where(AuthToken.token_hash == hash_token(token))
                .where(AuthToken.revoked_at.is_(None))
                .where(AuthToken.expires_at > now)
                .where(User.is_active.is_(True))
            ).scalar_one_or_none()

            if token_row:
                return token_row

            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired access token.",
            )

        if self._allow_legacy_user_header and x_user_id:
            user_id = x_user_id.strip()
            if self._legacy_pattern.match(user_id):
                return user_id
            raise HTTPException(
                status_code=400,
                detail="Invalid X-User-ID. Use 1-64 chars: letters, numbers, _, -, ., :, @",
            )

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing access token. Use Authorization: Bearer <token>.",
        )

    def _extract_bearer_token(self, authorization: Optional[str]) -> str:
        value = (authorization or "").strip()
        if not value:
            return ""
        scheme, _, token = value.partition(" ")
        if scheme.lower() != "bearer" or not token.strip():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Authorization header. Use Bearer token.",
            )
        return token.strip()


current_user_resolver = CurrentUserResolver()
