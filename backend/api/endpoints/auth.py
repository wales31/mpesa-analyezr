from __future__ import annotations

import re
import secrets
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import delete, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.api.dependencies import current_user_resolver
from backend.database import get_db
from backend.models import AuthToken, User
from backend.schemas import AuthResponse, AuthUserOut, LoginRequest, RegisterRequest
from backend.security import hash_password, hash_token, issue_access_token, token_expiry, verify_password


class AuthEndpoint:
    _username_pattern = re.compile(r"^[A-Za-z0-9_.-]{3,64}$")

    def register(self, router: APIRouter) -> None:
        router.add_api_route(
            "/auth/register",
            self.register_user,
            methods=["POST"],
            response_model=AuthResponse,
            status_code=status.HTTP_201_CREATED,
        )
        router.add_api_route(
            "/auth/login",
            self.login_user,
            methods=["POST"],
            response_model=AuthResponse,
        )
        router.add_api_route(
            "/auth/me",
            self.get_current_user,
            methods=["GET"],
            response_model=AuthUserOut,
        )

    async def register_user(
        self,
        req: RegisterRequest,
        db: Session = Depends(get_db),
    ) -> AuthResponse:
        email = self._normalize_email(req.email)
        username = self._normalize_username(req.username)

        if not email:
            raise HTTPException(status_code=400, detail="Invalid email address.")
        if not username:
            raise HTTPException(
                status_code=400,
                detail="Username must be 3-64 chars using letters, numbers, ., _, or -",
            )

        existing = db.execute(
            select(User).where(or_(User.email == email, User.username == username))
        ).scalars()
        for row in existing:
            if row.email == email:
                raise HTTPException(status_code=409, detail="Email is already registered.")
            if row.username == username:
                raise HTTPException(status_code=409, detail="Username is already taken.")

        try:
            password_hash = hash_password(req.password)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

        user = User(
            id=self._next_user_id(),
            email=email,
            username=username,
            password_hash=password_hash,
            is_active=True,
        )
        db.add(user)

        token_text = issue_access_token()
        expires_at = token_expiry()
        db.add(
            AuthToken(
                user_id=user.id,
                token_hash=hash_token(token_text),
                expires_at=expires_at,
            )
        )

        try:
            db.commit()
        except IntegrityError as exc:
            db.rollback()
            raise HTTPException(status_code=409, detail="Unable to register user.") from exc

        return AuthResponse(
            access_token=token_text,
            token_type="bearer",
            expires_at=expires_at,
            user=self._to_user_out(user),
        )

    async def login_user(
        self,
        req: LoginRequest,
        db: Session = Depends(get_db),
    ) -> AuthResponse:
        identifier = (req.identifier or "").strip().lower()
        if not identifier:
            raise HTTPException(status_code=400, detail="Identifier is required.")

        user = db.execute(
            select(User).where(or_(User.email == identifier, User.username == identifier))
        ).scalar_one_or_none()

        if not user or not user.is_active or not verify_password(req.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials.",
            )

        now = datetime.now(timezone.utc)
        db.execute(delete(AuthToken).where(AuthToken.expires_at < now))

        token_text = issue_access_token()
        expires_at = token_expiry()
        db.add(
            AuthToken(
                user_id=user.id,
                token_hash=hash_token(token_text),
                expires_at=expires_at,
            )
        )
        db.commit()

        return AuthResponse(
            access_token=token_text,
            token_type="bearer",
            expires_at=expires_at,
            user=self._to_user_out(user),
        )

    async def get_current_user(
        self,
        user_id: str = Depends(current_user_resolver.resolve),
        db: Session = Depends(get_db),
    ) -> AuthUserOut:
        user = db.get(User, user_id)
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid user.",
            )
        return self._to_user_out(user)

    def _to_user_out(self, user: User) -> AuthUserOut:
        return AuthUserOut(
            id=user.id,
            email=user.email,
            username=user.username,
        )

    def _normalize_email(self, email: str) -> str:
        value = (email or "").strip().lower()
        if "@" not in value or value.startswith("@") or value.endswith("@"):
            return ""
        local, _, domain = value.partition("@")
        if "." not in domain or not local or not domain:
            return ""
        return value

    def _normalize_username(self, username: str) -> str:
        value = (username or "").strip().lower()
        if not self._username_pattern.match(value):
            return ""
        return value

    def _next_user_id(self) -> str:
        return f"user_{secrets.token_hex(12)}"
