from __future__ import annotations

import os
from pathlib import Path
from typing import AsyncGenerator

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine.url import URL, make_url
from sqlalchemy.exc import OperationalError
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

    Note: MYSQL_* variables alone do not switch backends; set MPESA_DB_BACKEND=mysql
    (or provide a full DATABASE_URL) when you explicitly want MySQL.
    """

    url = (os.getenv("MPESA_DATABASE_URL") or os.getenv("DATABASE_URL") or "").strip()
    if url:
        return url

    backend = (os.getenv("MPESA_DB_BACKEND") or "").strip().lower()
    if backend in {"sqlite"}:
        return DEFAULT_SQLITE_URL
    if backend in {"mysql", "mariadb"}:
        return _build_mysql_url()

    return DEFAULT_SQLITE_URL


DATABASE_URL = resolve_database_url()
_url = make_url(DATABASE_URL)

engine_kwargs: dict[str, object] = {"pool_pre_ping": True}
if _url.get_backend_name() == "sqlite":
    engine_kwargs["connect_args"] = {"check_same_thread": False}

def _is_truthy(value: str | None) -> bool:
    return (value or "").strip().lower() in {"1", "true", "yes", "on"}


def _should_fallback_to_sqlite() -> bool:
    """
    Allow local development to keep working when a configured MySQL server
    is unavailable.

    Set MPESA_DB_FALLBACK_TO_SQLITE=0 to disable this behavior.
    """

    raw = os.getenv("MPESA_DB_FALLBACK_TO_SQLITE")
    if raw is None:
        return True
    return _is_truthy(raw)


def _create_engine_with_optional_fallback() -> tuple[str, object]:
    primary_url = DATABASE_URL
    primary_engine = create_engine(primary_url, **engine_kwargs)

    if _url.get_backend_name() not in {"mysql", "mariadb"}:
        return primary_url, primary_engine

    if not _should_fallback_to_sqlite():
        return primary_url, primary_engine

    try:
        with primary_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return primary_url, primary_engine
    except OperationalError:
        sqlite_url = DEFAULT_SQLITE_URL
        sqlite_engine = create_engine(
            sqlite_url,
            pool_pre_ping=True,
            connect_args={"check_same_thread": False},
        )
        print(
            "Warning: Unable to connect to configured MySQL database; "
            "falling back to SQLite. "
            "Set MPESA_DB_FALLBACK_TO_SQLITE=0 to disable fallback."
        )
        return sqlite_url, sqlite_engine


DATABASE_URL, engine = _create_engine_with_optional_fallback()

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
        if "raw_message" not in columns:
            conn.execute(text("ALTER TABLE transactions ADD COLUMN raw_message TEXT"))
            columns.add("raw_message")
        if "normalized_message" not in columns:
            conn.execute(text("ALTER TABLE transactions ADD COLUMN normalized_message TEXT"))
            columns.add("normalized_message")
        if "transaction_sub_type" not in columns:
            conn.execute(text("ALTER TABLE transactions ADD COLUMN transaction_sub_type VARCHAR(32)"))
            columns.add("transaction_sub_type")
        if "confidence_score" not in columns:
            conn.execute(text("ALTER TABLE transactions ADD COLUMN confidence_score NUMERIC(4,3)"))
            columns.add("confidence_score")
        if "classification_source" not in columns:
            conn.execute(text("ALTER TABLE transactions ADD COLUMN classification_source VARCHAR(32)"))
            columns.add("classification_source")
        if "matched_rule" not in columns:
            conn.execute(text("ALTER TABLE transactions ADD COLUMN matched_rule VARCHAR(255)"))
            columns.add("matched_rule")
        if "category_suggestions" not in columns:
            conn.execute(text("ALTER TABLE transactions ADD COLUMN category_suggestions VARCHAR(255)"))
            columns.add("category_suggestions")
        if "merchant_name" not in columns:
            conn.execute(text("ALTER TABLE transactions ADD COLUMN merchant_name VARCHAR(128)"))
            columns.add("merchant_name")
        if "contact_name" not in columns:
            conn.execute(text("ALTER TABLE transactions ADD COLUMN contact_name VARCHAR(128)"))
            columns.add("contact_name")
        if "paybill_number" not in columns:
            conn.execute(text("ALTER TABLE transactions ADD COLUMN paybill_number VARCHAR(32)"))
            columns.add("paybill_number")
        if "till_number" not in columns:
            conn.execute(text("ALTER TABLE transactions ADD COLUMN till_number VARCHAR(32)"))
            columns.add("till_number")
        if "account_reference" not in columns:
            conn.execute(text("ALTER TABLE transactions ADD COLUMN account_reference VARCHAR(128)"))
            columns.add("account_reference")
        if "user_corrected_category" not in columns:
            conn.execute(text("ALTER TABLE transactions ADD COLUMN user_corrected_category VARCHAR(64)"))
            columns.add("user_corrected_category")
        if "user_correction_key" not in columns:
            conn.execute(text("ALTER TABLE transactions ADD COLUMN user_correction_key VARCHAR(255)"))
            columns.add("user_correction_key")
        for ddl_name, ddl in [
            ("matched_priority_tier", "ALTER TABLE transactions ADD COLUMN matched_priority_tier INTEGER"),
            ("matched_key_type", "ALTER TABLE transactions ADD COLUMN matched_key_type VARCHAR(64)"),
            ("correction_scope", "ALTER TABLE transactions ADD COLUMN correction_scope VARCHAR(64)"),
            ("correction_match_basis", "ALTER TABLE transactions ADD COLUMN correction_match_basis VARCHAR(64)"),
            ("canonical_entity_name", "ALTER TABLE transactions ADD COLUMN canonical_entity_name VARCHAR(128)"),
            ("normalized_text_signature", "ALTER TABLE transactions ADD COLUMN normalized_text_signature VARCHAR(255)"),
            ("confidence_band", "ALTER TABLE transactions ADD COLUMN confidence_band VARCHAR(16)"),
            ("confidence_breakdown", "ALTER TABLE transactions ADD COLUMN confidence_breakdown TEXT"),
            ("confidence_reason_summary", "ALTER TABLE transactions ADD COLUMN confidence_reason_summary VARCHAR(255)"),
            ("conflict_flag", "ALTER TABLE transactions ADD COLUMN conflict_flag BOOLEAN"),
            ("conflict_reasons", "ALTER TABLE transactions ADD COLUMN conflict_reasons TEXT"),
            ("competing_rules", "ALTER TABLE transactions ADD COLUMN competing_rules TEXT"),
            ("needs_review", "ALTER TABLE transactions ADD COLUMN needs_review BOOLEAN"),
        ]:
            if ddl_name not in columns:
                conn.execute(text(ddl))
                columns.add(ddl_name)

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
        if "ix_transactions_paybill_number" not in indexes:
            conn.execute(text("CREATE INDEX ix_transactions_paybill_number ON transactions (paybill_number)"))
        if "ix_transactions_till_number" not in indexes:
            conn.execute(text("CREATE INDEX ix_transactions_till_number ON transactions (till_number)"))
        if "ix_transactions_user_correction_key" not in indexes:
            conn.execute(
                text(
                    "CREATE INDEX ix_transactions_user_correction_key "
                    "ON transactions (user_id, user_correction_key)"
                )
            )

        if inspector.has_table("category_learning_rules"):
            learning_columns = {col["name"] for col in inspector.get_columns("category_learning_rules")}
            for ddl_name, ddl in [
                ("correction_scope", "ALTER TABLE category_learning_rules ADD COLUMN correction_scope VARCHAR(64)"),
                ("correction_match_basis", "ALTER TABLE category_learning_rules ADD COLUMN correction_match_basis VARCHAR(64)"),
                ("canonical_entity_name", "ALTER TABLE category_learning_rules ADD COLUMN canonical_entity_name VARCHAR(128)"),
                ("normalized_text_signature", "ALTER TABLE category_learning_rules ADD COLUMN normalized_text_signature VARCHAR(255)"),
                ("is_manual", "ALTER TABLE category_learning_rules ADD COLUMN is_manual BOOLEAN NOT NULL DEFAULT 0"),
            ]:
                if ddl_name not in learning_columns:
                    conn.execute(text(ddl))


def display_database_url() -> str:
    """Safe-to-print database URL (password hidden when possible)."""

    try:
        return make_url(DATABASE_URL).render_as_string(hide_password=True)
    except Exception:
        return DATABASE_URL
