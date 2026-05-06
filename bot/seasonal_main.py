"""月次の「先輩からのひとこと」を国内チャンネルへ投稿するエントリポイント。

GitHub Actions cron で毎月1日に呼ぶ。該当月のコンテンツが無ければ何もしない。
"""
from __future__ import annotations

import sys

from datetime import date

from . import config, seasonal_tips
from .discord_post import _post_content


def main() -> int:
    tip = seasonal_tips.current_tip()
    if not tip:
        print("[seasonal] no tip for this month, skipping")
        return 0

    month = date.today().month
    msg = f"✍️ **【うめこの4年生・{month}月の日記】**\n\n{tip}"

    if not config.WEBHOOK_DOMESTIC:
        print("[seasonal] DISCORD_WEBHOOK_DOMESTIC empty, skipping")
        return 0

    _post_content(config.WEBHOOK_DOMESTIC, msg)
    print("[seasonal] posted tip for this month")
    return 0


if __name__ == "__main__":
    sys.exit(main())
