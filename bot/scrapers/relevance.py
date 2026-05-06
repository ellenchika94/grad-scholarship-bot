"""通知すべき奨学金かを判定するルール群。"""
from __future__ import annotations

import re
from datetime import date, timedelta


def is_master_relevant(target: str | None) -> bool:
    """修士向けでない（博士のみ／高校生のみ／学部のみ）と判定されるなら False。

    target に「修士」が含まれていれば常に True。
    含まれていない場合、博士／高校生／学部だけが含まれていれば False。
    target が無い場合は不明として True（通す）。
    """
    if not target:
        return True
    if "修士" in target:
        return True
    if "博士" in target or "高校生" in target or "学部" in target:
        return False
    return True


_MONTH_RE = re.compile(r"(?<!\d)(\d{1,2})月")


def has_seasonal_window_within(deadline_note: str | None, days: int, today: date | None = None) -> bool:
    """deadline_noteから「X月」を拾い、次回到来が `days` 日以内ならTrue。

    月の指定が無い／全部過去すぎる場合は True を返す（情報不明として通す）。
    """
    if not deadline_note:
        return True
    today = today or date.today()
    months = [int(m) for m in _MONTH_RE.findall(deadline_note)]
    if not months:
        return True
    candidates: list[date] = []
    for m in months:
        if not 1 <= m <= 12:
            continue
        # 今年/来年で最も近い未来の中旬
        yr = today.year if m >= today.month else today.year + 1
        try:
            candidates.append(date(yr, m, 15))
        except ValueError:
            continue
    if not candidates:
        return True
    nearest = min(candidates)
    return (nearest - today).days <= days
