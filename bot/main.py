"""Orchestrator: fetch all sources, store new items, dispatch Discord notifications."""
from __future__ import annotations

import sys
import traceback

from . import config, db, discord_post
from .scrapers import ALL_SCRAPERS


def _row_to_item(row) -> dict:
    return {
        "title": row["title"],
        "url": row["url"],
        "deadline": row["deadline"],
        "source_label": _label_for_source(row["source"]),
    }


def _label_for_source(source_id: str) -> str:
    for scraper in ALL_SCRAPERS:
        if scraper.source_id == source_id:
            return scraper.source_label
    return source_id


def collect_new(conn) -> dict[str, int]:
    counts: dict[str, int] = {}
    for scraper in ALL_SCRAPERS:
        try:
            items = list(scraper.fetch())
        except Exception:
            print(f"[error] scraper {scraper.source_id} failed:", file=sys.stderr)
            traceback.print_exc()
            counts[scraper.source_id] = -1
            continue
        new_count = 0
        for item in items:
            inserted = db.upsert_scholarship(
                conn,
                source=scraper.source_id,
                external_id=item.external_id,
                title=item.title,
                url=item.url,
                deadline=item.deadline,
                region=item.region,
            )
            if inserted:
                new_count += 1
        counts[scraper.source_id] = new_count
        print(f"[ok] {scraper.source_id}: fetched={len(items)} new={new_count}")
    return counts


def notify_new(conn) -> None:
    for region in ("domestic", "overseas"):
        rows = db.fetch_unnotified(conn, region)
        if not rows:
            continue
        items = [_row_to_item(r) for r in rows]
        try:
            discord_post.post_new(region, items)
            for r in rows:
                db.mark_notified(conn, r["id"])
            print(f"[ok] notified region={region} count={len(rows)}")
        except Exception:
            print(f"[error] notify_new region={region} failed:", file=sys.stderr)
            traceback.print_exc()


def notify_reminders(conn) -> None:
    for days in config.REMINDER_DAYS:
        for region in ("domestic", "overseas"):
            rows = db.fetch_due_for_reminder(conn, days, region)
            if not rows:
                continue
            items = [_row_to_item(r) for r in rows]
            try:
                discord_post.post_reminders(region, items, days)
                for r in rows:
                    db.mark_reminder_sent(conn, r["id"], days)
                print(f"[ok] reminder {days}d region={region} count={len(rows)}")
            except Exception:
                print(f"[error] reminder {days}d region={region} failed:", file=sys.stderr)
                traceback.print_exc()


def main() -> int:
    with db.connect() as conn:
        counts = collect_new(conn)
        notify_new(conn)
        notify_reminders(conn)
    summary = ", ".join(f"{k}={v}" for k, v in counts.items())
    print(f"[summary] new items per source: {summary}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
