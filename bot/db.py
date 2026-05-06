import sqlite3
from contextlib import contextmanager
from datetime import date, datetime
from typing import Iterator

from . import config

SCHEMA = """
CREATE TABLE IF NOT EXISTS scholarships (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source TEXT NOT NULL,
    external_id TEXT NOT NULL,
    title TEXT NOT NULL,
    url TEXT NOT NULL,
    deadline DATE,
    deadline_note TEXT,
    region TEXT NOT NULL CHECK(region IN ('domestic','overseas')),
    first_seen_at TEXT NOT NULL,
    notified_new INTEGER NOT NULL DEFAULT 0,
    reminder_7_sent INTEGER NOT NULL DEFAULT 0,
    reminder_3_sent INTEGER NOT NULL DEFAULT 0,
    UNIQUE(source, external_id)
);
CREATE INDEX IF NOT EXISTS idx_scholarships_deadline ON scholarships(deadline);
"""

_MIGRATIONS = [
    "ALTER TABLE scholarships ADD COLUMN deadline_note TEXT",
    "ALTER TABLE scholarships ADD COLUMN amount TEXT",
    "ALTER TABLE scholarships ADD COLUMN target TEXT",
    "ALTER TABLE scholarships ADD COLUMN scholarship_type TEXT",
    "ALTER TABLE scholarships ADD COLUMN official_url TEXT",
]


def _apply_migrations(conn: sqlite3.Connection) -> None:
    for stmt in _MIGRATIONS:
        try:
            conn.execute(stmt)
        except sqlite3.OperationalError:
            pass


@contextmanager
def connect() -> Iterator[sqlite3.Connection]:
    config.DATA_DIR.mkdir(exist_ok=True)
    conn = sqlite3.connect(config.DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        conn.executescript(SCHEMA)
        _apply_migrations(conn)
        yield conn
        conn.commit()
    finally:
        conn.close()


def is_known(conn: sqlite3.Connection, source: str, external_id: str) -> bool:
    cur = conn.execute(
        "SELECT 1 FROM scholarships WHERE source = ? AND external_id = ?",
        (source, external_id),
    )
    return cur.fetchone() is not None


def upsert_scholarship(
    conn: sqlite3.Connection,
    source: str,
    external_id: str,
    title: str,
    url: str,
    deadline: date | None,
    region: str,
    deadline_note: str | None = None,
    amount: str | None = None,
    target: str | None = None,
    scholarship_type: str | None = None,
    official_url: str | None = None,
) -> bool:
    """Insert if new. Returns True when newly inserted."""
    if is_known(conn, source, external_id):
        return False
    conn.execute(
        """
        INSERT INTO scholarships (
            source, external_id, title, url, deadline, deadline_note,
            amount, target, scholarship_type, official_url, region, first_seen_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (source, external_id, title, url, deadline, deadline_note,
         amount, target, scholarship_type, official_url, region,
         datetime.utcnow().isoformat()),
    )
    return True


def fetch_unnotified(conn: sqlite3.Connection, region: str) -> list[sqlite3.Row]:
    """未通知のうち、締切が今日から3ヶ月以内 or 締切不明のものを返す。

    締切がそれより先のものは、後の実行で3ヶ月窓に入ったら通知される。
    """
    return list(
        conn.execute(
            """
            SELECT * FROM scholarships
            WHERE notified_new = 0
              AND region = ?
              AND (
                deadline IS NULL
                OR (date(deadline) >= date('now')
                    AND date(deadline) <= date('now', '+3 months'))
              )
            ORDER BY COALESCE(deadline, '9999-12-31'), id
            """,
            (region,),
        )
    )


def mark_notified(conn: sqlite3.Connection, scholarship_id: int) -> None:
    conn.execute(
        "UPDATE scholarships SET notified_new = 1 WHERE id = ?", (scholarship_id,)
    )


def fetch_upcoming(
    conn: sqlite3.Connection,
    region: str,
    days: int,
    exclude_ids: set[int] | None = None,
) -> list[sqlite3.Row]:
    """締切が今日〜N日後にある奨学金を取得（締切間近リマインダ用）。

    既通知/新規通知に関わらず、締切が窓に入っているものを毎回返す。
    `exclude_ids` には「同じ実行回で新着として通知済」のIDを渡し、
    新着セクションと締切間近セクションでの二重表示を防ぐ。
    """
    rows = list(
        conn.execute(
            f"""
            SELECT * FROM scholarships
            WHERE region = ?
              AND deadline IS NOT NULL
              AND date(deadline) >= date('now')
              AND date(deadline) <= date('now', '+{days} days')
            ORDER BY date(deadline), id
            """,
            (region,),
        )
    )
    if exclude_ids:
        rows = [r for r in rows if r["id"] not in exclude_ids]
    return rows
