import time
from datetime import date

import requests

from . import config, umeko


DISCLAIMER = (
    "※ このBotは奨学金情報サイトを巡回した結果を自動投稿しています。"
    "**実際の募集要項・最新情報は必ず各公式サイトでご確認ください。**"
)
ITEM_SEPARATOR = "\n\n\n"  # 奨学金間に2行の空行
MAX_CONTENT = 1800           # Discord 2000文字制限の安全マージン


def _trim_note(text: str, limit: int = 70) -> str:
    text = text.strip()
    return text if len(text) <= limit else text[: limit - 1] + "…"


def _format_deadline_inline(deadline, note: str | None = None) -> str:
    # 国内の「中旬/上旬/下旬」表記は note に原文が入る → そちらを表示
    if deadline and note:
        return _trim_note(note)
    if deadline:
        if isinstance(deadline, date):
            return deadline.strftime("%Y-%m-%d")
        return str(deadline)
    if note:
        # 海外（XPLANE）の例年情報。締切日が無いケース
        return f"（例年）{_trim_note(note)}"
    return "要確認（リンク先参照）"


def _format_item(item: dict) -> str:
    lines = [f"**▸ {item['title']}**"]
    if item.get("target"):
        lines.append(f"対象：{item['target']}")
    if item.get("amount"):
        lines.append(f"額面：{item['amount']}")
    if item.get("scholarship_type"):
        lines.append(f"種別：{item['scholarship_type']}")
    lines.append(f"締切：{_format_deadline_inline(item.get('deadline'), item.get('deadline_note'))}")
    # 出典・公式URLともに <> で囲んでDiscordの自動プレビュー展開を抑制
    lines.append(f"出典：<{item['url']}>")
    main_url = item.get("official_url") or item["url"]
    lines.append(f"公式URL：<{main_url}>")
    return "\n".join(lines)


def _post_content(webhook_url: str, content: str) -> None:
    if not webhook_url:
        print("[discord] webhook URL empty, skipping")
        return
    resp = requests.post(
        webhook_url,
        json={"content": content},
        headers={"User-Agent": config.USER_AGENT},
        timeout=15,
    )
    resp.raise_for_status()
    time.sleep(1)


def _post_items(webhook_url: str, header: str, items: list[dict]) -> None:
    """ヘッダ（バナー＋免責）→ 奨学金チャンク（複数メッセージに分割）。"""
    _post_content(webhook_url, header)

    chunk: list[str] = []
    chunk_len = 0
    sep_len = len(ITEM_SEPARATOR)
    for item in items:
        text = _format_item(item)
        proposed = chunk_len + (sep_len if chunk else 0) + len(text)
        if chunk and proposed > MAX_CONTENT:
            _post_content(webhook_url, ITEM_SEPARATOR.join(chunk))
            chunk = [text]
            chunk_len = len(text)
        else:
            chunk.append(text)
            chunk_len = proposed
    if chunk:
        _post_content(webhook_url, ITEM_SEPARATOR.join(chunk))


def post_new(region: str, items: list[dict]) -> None:
    if not items:
        return
    webhook = config.WEBHOOK_DOMESTIC if region == "domestic" else config.WEBHOOK_OVERSEAS
    header = (
        "━━━━━━━━━━━━━━━━━━━━\n"
        "🆕 **【新着情報】3ヶ月以内に締切予定の奨学金情報です**\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"{DISCLAIMER}"
    )
    _post_items(webhook, header, items)


def post_umeko(region: str) -> None:
    """各回の最後に「うめこのひとこと」を投稿。"""
    webhook = config.WEBHOOK_DOMESTIC if region == "domestic" else config.WEBHOOK_OVERSEAS
    msg = (
        "━━━━━━━━━━━━━━━━━━━━\n"
        "💌 **今日のうめこのひとこと**\n"
        f"{umeko.random_message()}"
    )
    _post_content(webhook, msg)


def post_upcoming(region: str, items: list[dict], days: int) -> None:
    """締切間近セクション。今日〜N日後に締切のものを毎回掲載。"""
    if not items:
        return
    webhook = config.WEBHOOK_DOMESTIC if region == "domestic" else config.WEBHOOK_OVERSEAS
    header = (
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"⏰ **【締切間近】{days}日以内に締切の奨学金です**\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"{DISCLAIMER}"
    )
    _post_items(webhook, header, items)
