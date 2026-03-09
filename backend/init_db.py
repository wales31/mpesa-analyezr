from __future__ import annotations

from pathlib import Path
import sys

from sqlalchemy.exc import OperationalError


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(repo_root))

    from backend.database import display_database_url, init_db

    try:
        init_db()
    except OperationalError as exc:
        print(f"Failed to initialize database: {display_database_url()}")
        print()
        print("Unable to connect to the configured database server.")
        print("If MySQL is not running, start it or use SQLite instead:")
        print("  MPESA_DB_BACKEND=sqlite python backend/init_db.py")
        raise SystemExit(1) from exc

    print(f"Initialized database: {display_database_url()}")


if __name__ == "__main__":
    main()
