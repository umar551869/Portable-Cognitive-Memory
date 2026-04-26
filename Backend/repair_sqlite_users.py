from __future__ import annotations

import sqlite3


def main() -> None:
    conn = sqlite3.connect("pcg.db")
    cur = conn.cursor()
    cur.execute(
        """
        SELECT DISTINCT user_id FROM (
            SELECT user_id FROM raw_logs
            UNION
            SELECT user_id FROM chunks
            UNION
            SELECT user_id FROM nodes
            UNION
            SELECT user_id FROM edges
            UNION
            SELECT user_id FROM embeddings
        )
        WHERE user_id IS NOT NULL
        """
    )
    user_ids = [row[0] for row in cur.fetchall()]

    repaired = 0
    for user_id in user_ids:
        cur.execute("SELECT 1 FROM users WHERE id = ?", (user_id,))
        if cur.fetchone():
            continue
        email = f"recovered-{user_id}@local.invalid"
        cur.execute(
            "INSERT INTO users (id, name, email, password_hash, is_admin, created_at) VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)",
            (user_id, "Recovered User", email, "recovered-local-account", 0),
        )
        repaired += 1

    conn.commit()
    conn.close()
    print(f"Repaired {repaired} missing users.")


if __name__ == "__main__":
    main()
