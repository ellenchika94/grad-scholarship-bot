"""月次の「先輩からのひとこと」を海外組チャンネルへ投稿するエントリポイント。

GitHub Actions cron で毎月1日に呼ぶ。3年生・4年生のメッセージを1投稿にまとめる。
"""
from __future__ import annotations

import sys

from datetime import date

from . import config, seasonal_tips_overseas
from .discord_post import _post_content


def main() -> int:
    tip_3rd, tip_4th = seasonal_tips_overseas.current_tips()
    if not tip_3rd and not tip_4th:
        print("[seasonal-overseas] no tip for this month, skipping")
        return 0

    month = date.today().month
    sections: list[str] = []
    if tip_3rd:
        sections.append(f"✍️ **【うめこの3年生・{month}月の日記】**\n\n{tip_3rd}")
    if tip_4th:
        sections.append(f"✍️ **【うめこの4年生・{month}月の日記】**\n\n{tip_4th}")
    msg = "\n\n―――\n\n".join(sections)

    if not config.WEBHOOK_OVERSEAS:
        print("[seasonal-overseas] DISCORD_WEBHOOK_OVERSEAS empty, skipping")
        return 0

    _post_content(config.WEBHOOK_OVERSEAS, msg)
    print("[seasonal-overseas] posted tips for this month")
    return 0


if __name__ == "__main__":
    sys.exit(main())
