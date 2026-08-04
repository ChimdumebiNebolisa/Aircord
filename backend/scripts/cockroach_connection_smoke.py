from __future__ import annotations

import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aircord.db.connection import connect_database  # noqa: E402


def main() -> None:
    try:
        with connect_database() as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT current_database(), now();")
                database, current_time = cursor.fetchone()
        print(f"CockroachDB connection succeeded: database={database}, now={current_time}")
    except Exception as exc:
        raise SystemExit(f"CockroachDB connection smoke failed: {type(exc).__name__}") from exc


if __name__ == "__main__":
    main()
