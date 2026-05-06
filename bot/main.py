"""Orchestrator: fetch all sources, store new items, dispatch Discord notifications."""
from __future__ import annotations

import sys
import traceback

from . import config, db, discord_post
from .scrapers import ALL_SCRAPERS
from .scrapers.relevance import has_seasonal_window_within, is_master_relevant


def _mark_existing_notified(conn, source_id: str, external_id: str) -> None:
    row = conn.execute(
        "SELECT id FROM scholarships WHERE source = ? AND external_id = ?",
        (source_id, external_id),
    ).fetchone()
    if row:
        db.mark_notified(conn, row[0])


def _row_to_item(row) -> dict:
    keys = row.keys()
    return {
        "title": row["title"],
        "url": row["url"],
        "official_url": row["official_url"] if "official_url" in keys else None,
        "deadline": row["deadline"],
        "deadline_note": row["deadline_note"] if "deadline_note" in keys else None,
        "amount": row["amount"] if "amount" in keys else None,
        "target": row["target"] if "target" in keys else None,
        "scholarship_type": row["scholarship_type"] if "scholarship_type" in keys else None,
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
            # 既知ならenrichをスキップ（個別ページfetchを回避）
            if db.is_known(conn, scraper.source_id, item.external_id):
                continue
            try:
                item = scraper.enrich(item)
            except Exception:
                print(f"[warn] enrich failed for {scraper.source_id}/{item.external_id}", file=sys.stderr)
                traceback.print_exc()
            db.upsert_scholarship(
                conn,
                source=scraper.source_id,
                external_id=item.external_id,
                title=item.title,
                url=item.url,
                deadline=item.deadline,
                region=item.region,
                deadline_note=item.deadline_note,
                amount=item.amount,
                target=item.target,
                scholarship_type=item.scholarship_type,
                official_url=item.official_url,
            )
            # 修士向け以外（博士のみ等）はDBには保存するが通知済み扱いにして
            # 二度と通知しない（enrich結果のキャッシュは活かす）
            if not is_master_relevant(item.target):
                _mark_existing_notified(conn, scraper.source_id, item.external_id)
                print(f"  [skip:not-master] {item.title[:40]}")
                continue
            # XPLANEのように deadline=None で例年情報のみのケースは
            # deadline_noteから月を抜き出して3ヶ月以内に到来する分だけ通知対象に
            if item.deadline is None and item.deadline_note:
                if not has_seasonal_window_within(item.deadline_note, 90):
                    _mark_existing_notified(conn, scraper.source_id, item.external_id)
                    print(f"  [skip:>3mo] {item.title[:40]}")
                    continue
            new_count += 1
        counts[scraper.source_id] = new_count
        print(f"[ok] {scraper.source_id}: fetched={len(items)} new={new_count}")
    return counts


def notify_new(conn) -> dict[str, set[int]]:
    """新着通知。各regionで通知したIDのsetを返す（締切間近セクションでの除外用）。"""
    notified_ids: dict[str, set[int]] = {"domestic": set(), "overseas": set()}
    for region in ("domestic", "overseas"):
        rows = db.fetch_unnotified(conn, region)
        if not rows:
            continue
        items = [_row_to_item(r) for r in rows]
        try:
            discord_post.post_new(region, items)
            for r in rows:
                db.mark_notified(conn, r["id"])
                notified_ids[region].add(r["id"])
            print(f"[ok] notified region={region} count={len(rows)}")
        except Exception:
            print(f"[error] notify_new region={region} failed:", file=sys.stderr)
            traceback.print_exc()
    return notified_ids


def notify_upcoming(conn, exclude_ids: dict[str, set[int]]) -> None:
    """締切間近（2週間以内）の奨学金を毎回通知。新着で出したものは除外。"""
    days = config.UPCOMING_DAYS
    for region in ("domestic", "overseas"):
        rows = db.fetch_upcoming(conn, region, days, exclude_ids.get(region))
        if not rows:
            continue
        items = [_row_to_item(r) for r in rows]
        try:
            discord_post.post_upcoming(region, items, days)
            print(f"[ok] upcoming {days}d region={region} count={len(rows)}")
        except Exception:
            print(f"[error] upcoming region={region} failed:", file=sys.stderr)
            traceback.print_exc()


def post_umeko_for_active_regions(notified_ids: dict[str, set[int]], conn) -> None:
    """このrunで何か投稿があったregionにだけ、うめこのひとこと送る。"""
    for region in ("domestic", "overseas"):
        had_new = bool(notified_ids.get(region))
        # upcomingがあった場合も送りたいので、そのチェックも兼ねる
        had_upcoming = bool(db.fetch_upcoming(conn, region, config.UPCOMING_DAYS, notified_ids.get(region)))
        if had_new or had_upcoming:
            try:
                discord_post.post_umeko(region)
            except Exception:
                print(f"[error] post_umeko region={region} failed:", file=sys.stderr)
                traceback.print_exc()


def main() -> int:
    with db.connect() as conn:
        counts = collect_new(conn)
        notified_ids = notify_new(conn)
        notify_upcoming(conn, notified_ids)
        post_umeko_for_active_regions(notified_ids, conn)
    summary = ", ".join(f"{k}={v}" for k, v in counts.items())
    print(f"[summary] new items per source: {summary}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
