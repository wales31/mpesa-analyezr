from __future__ import annotations

import os
from pathlib import Path
from typing import AsyncGenerator

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine.url import URL, make_url
from sqlalchemy.orm import Session, declarative_base, sessionmaker

BASE_DIR = Path(__file__).resolve().parent

DEFAULT_SQLITE_PATH = BASE_DIR / "database.db"
DEFAULT_SQLITE_URL = f"sqlite:///{DEFAULT_SQLITE_PATH.as_posix()}"


def _build_mysql_url() -> str:
    """
    Build a MySQL/MariaDB SQLAlchemy URL from environment variables.

    This matches common local XAMPP defaults (root@127.0.0.1:3306).
    """

    user = os.getenv("MYSQL_USER", "root")
    password = os.getenv("MYSQL_PASSWORD", "")
    host = os.getenv("MYSQL_HOST", "127.0.0.1")
    port = int(os.getenv("MYSQL_PORT", "3306"))
    database = os.getenv("MYSQL_DATABASE", "mpesa_analyzer")

    return str(
        URL.create(
            drivername="mysql+pymysql",
            username=user or None,
            password=password or None,
            host=host,
            port=port,
            database=database,
            query={"charset": "utf8mb4"},
        )
    )


def resolve_database_url() -> str:
    """
    Resolve database URL with the following precedence:

    1) MPESA_DATABASE_URL / DATABASE_URL (full SQLAlchemy URL)
    2) MPESA_DB_BACKEND=mysql|mariadb (build from MYSQL_* vars)
    3) SQLite file under backend/ (default)
    """

    url = (os.getenv("MPESA_DATABASE_URL") or os.getenv("DATABASE_URL") or "").strip()
    if url:
        return url

    backend = (os.getenv("MPESA_DB_BACKEND") or "").strip().lower()
    if backend in {"sqlite"}:
        return DEFAULT_SQLITE_URL
    if backend in {"mysql", "mariadb"}:
        return _build_mysql_url()

    mysql_hint = any(
        (os.getenv(key) or "").strip()
        for key in (
            "MYSQL_HOST",
            "MYSQL_PORT",
            "MYSQL_USER",
            "MYSQL_PASSWORD",
            "MYSQL_DATABASE",
        )
    )
    if mysql_hint:
        return _build_mysql_url()

    return DEFAULT_SQLITE_URL


DATABASE_URL = resolve_database_url()
_url = make_url(DATABASE_URL)

engine_kwargs: dict[str, object] = {"pool_pre_ping": True}
if _url.get_backend_name() == "sqlite":
    engine_kwargs["connect_args"] = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, **engine_kwargs)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


async def get_db() -> AsyncGenerator[Session, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    # Import models so they register with SQLAlchemy's metadata before create_all.
    import backend.models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    _apply_lightweight_migrations()


def _apply_lightweight_migrations() -> None:
    """
    Keep compatibility with existing local DB files that predate user scoping.
    """
    with engine.begin() as conn:
        inspector = inspect(conn)
        if not inspector.has_table("transactions"):
            return

        columns = {col["name"] for col in inspector.get_columns("transactions")}
        if "user_id" not in columns:
            conn.execute(
                text(
                    "ALTER TABLE transactions "
                    "ADD COLUMN user_id VARCHAR(64) NOT NULL DEFAULT 'default'"
                )
            )
            columns.add("user_id")

        if "ingestion_mode" not in columns:
            conn.execute(
                text(
                    "ALTER TABLE transactions "
                    "ADD COLUMN ingestion_mode VARCHAR(32) NOT NULL DEFAULT 'single_upload'"
                )
            )
            columns.add("ingestion_mode")

        if "ingestion_batch_id" not in columns:
            conn.execute(
                text(
                    "ALTER TABLE transactions "
                    "ADD COLUMN ingestion_batch_id VARCHAR(64)"
                )
            )
            columns.add("ingestion_batch_id")

        if "source_message_id" not in columns:
            conn.execute(
                text(
                    "ALTER TABLE transactions "
                    "ADD COLUMN source_message_id VARCHAR(128)"
                )
            )
            columns.add("source_message_id")

        if "source_received_at" not in columns:
            conn.execute(
                text(
                    "ALTER TABLE transactions "
                    "ADD COLUMN source_received_at DATETIME"
                )
            )
            columns.add("source_received_at")

        indexes = {idx["name"] for idx in inspector.get_indexes("transactions")}
        if "ix_transactions_user_id" not in indexes:
            conn.execute(text("CREATE INDEX ix_transactions_user_id ON transactions (user_id)"))
            indexes.add("ix_transactions_user_id")

        if "ix_transactions_source_message_id" not in indexes:
            conn.execute(
                text(
                    "CREATE INDEX ix_transactions_source_message_id "
                    "ON transactions (user_id, source_message_id)"
                )
            )
            indexes.add("ix_transactions_source_message_id")

        if "ix_transactions_ingestion_mode" not in indexes:
            conn.execute(
                text("CREATE INDEX ix_transactions_ingestion_mode ON transactions (ingestion_mode)")
            )
            indexes.add("ix_transactions_ingestion_mode")

        if "ix_transactions_ingestion_batch_id" not in indexes:
            conn.execute(
                text(
                    "CREATE INDEX ix_transactions_ingestion_batch_id "
                    "ON transactions (ingestion_batch_id)"
                )
            )


def display_database_url() -> str:
    """Safe-to-print database URL (password hidden when possible)."""

    try:
        return make_url(DATABASE_URL).render_as_string(hide_password=True)
    except Exception:
        return DATABASE_URL
