import time
from datetime import date

import requests

from . import config


def _format_deadline(deadline: date | None) -> str:
    if deadline is None:
        return "締切：要確認（リンク先参照）"
    return f"締切：{deadline.strftime('%Y-%m-%d')}"


def _send(webhook_url: str, embeds: list[dict]) -> None:
    if not webhook_url:
        print("[discord] webhook URL empty, skipping")
        return
    for chunk_start in range(0, len(embeds), 10):
        chunk = embeds[chunk_start : chunk_start + 10]
        resp = requests.post(
            webhook_url,
            json={"embeds": chunk},
            headers={"User-Agent": config.USER_AGENT},
            timeout=15,
        )
        resp.raise_for_status()
        time.sleep(1)


def post_new(region: str, items: list[dict]) -> None:
    if not items:
        return
    webhook = config.WEBHOOK_DOMESTIC if region == "domestic" else config.WEBHOOK_OVERSEAS
    label = "国内" if region == "domestic" else "海外"
    embeds = [
        {
            "title": f"[新着] {item['title']}",
            "url": item["url"],
            "description": (
                f"{_format_deadline(item.get('deadline'))}\n"
                f"出典：{item['source_label']}（{label}）"
            ),
            "color": 0x4CAF50,
        }
        for item in items
    ]
    _send(webhook, embeds)


def post_reminders(region: str, items: list[dict], days_ahead: int) -> None:
    if not items:
        return
    webhook = config.WEBHOOK_DOMESTIC if region == "domestic" else config.WEBHOOK_OVERSEAS
    embeds = [
        {
            "title": f"[締切{days_ahead}日前] {item['title']}",
            "url": item["url"],
            "description": (
                f"{_format_deadline(item.get('deadline'))}\n"
                f"出典：{item['source_label']}"
            ),
            "color": 0xFF9800 if days_ahead == 7 else 0xF44336,
        }
        for item in items
    ]
    _send(webhook, embeds)
