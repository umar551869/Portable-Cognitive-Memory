from __future__ import annotations

import sqlite3


def ensure_column(cursor: sqlite3.Cursor, table: str, column: str, ddl: str) -> None:
    cursor.execute(f"PRAGMA table_info({table})")
    existing = {row[1] for row in cursor.fetchall()}
    if column not in existing:
        cursor.execute(f"ALTER TABLE {table} ADD COLUMN {ddl}")


def main() -> None:
    conn = sqlite3.connect("pcg.db")
    cur = conn.cursor()
    ensure_column(cur, "users", "name", "name TEXT NOT NULL DEFAULT 'Recovered User'")
    ensure_column(cur, "users", "is_admin", "is_admin INTEGER NOT NULL DEFAULT 0")

    cur.execute("UPDATE users SET name = 'Recovered User' WHERE name IS NULL OR TRIM(name) = ''")
    cur.execute("UPDATE users SET is_admin = 0 WHERE is_admin IS NULL")

    conn.commit()
    conn.close()
    print("Users table migration complete.")


if __name__ == "__main__":
    main()
