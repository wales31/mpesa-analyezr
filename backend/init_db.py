from __future__ import annotations

from pathlib import Path
import sys


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(repo_root))

    from backend.database import display_database_url, init_db

    init_db()
    print(f"Initialized database: {display_database_url()}")


if __name__ == "__main__":
    main()
