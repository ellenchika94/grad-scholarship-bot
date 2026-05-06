import re
from typing import Iterable

from bs4 import BeautifulSoup

from .base import Scraper, ScholarshipItem
from .tagging import extract_tags


_DEADLINE_LABELS = ("選考日程", "応募期限", "応募締切", "出願期間", "募集期間", "申込期限", "締切")
_AMOUNT_LABELS = ("支給金額", "支給額", "奨学金額", "支援金額", "金額")
_TARGET_LABELS = ("応募資格", "対象", "所属指定", "留学先課程指定", "分野指定")
_OFFICIAL_LABELS = ("公式ウェブサイト", "公式サイト", "公式HP", "ホームページ")


def _trim(text: str, limit: int = 100) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    return text if len(text) <= limit else text[: limit - 1] + "…"


class Xplane(Scraper):
    """XPLANEは個別ページから例年の締切傾向＋額面＋対象を取得する。"""

    source_id = "xplane"
    source_label = "XPLANE"
    region = "overseas"
    feed_url = "https://xplane.jp/feed/?post_type=fellowship"

    def fetch(self) -> Iterable[ScholarshipItem]:
        feed = self.parse_feed(self.feed_url)
        for entry in feed.entries:
            external_id = entry.get("id") or entry.get("link")
            if not external_id:
                continue
            yield ScholarshipItem(
                external_id=external_id,
                title=entry.title,
                url=entry.link,
                deadline=None,
                scholarship_type="給付型",  # XPLANEは留学奨学金=fellowship、基本給付
                region=self.region,
            )

    def enrich(self, item: ScholarshipItem) -> ScholarshipItem:
        details = self._fetch_details(item.url)
        item.deadline_note = details.get("deadline_note")
        item.amount = details.get("amount")
        item.target = details.get("target")
        item.official_url = details.get("official_url")
        return item

    def _fetch_details(self, url: str) -> dict[str, str]:
        out: dict[str, str] = {}
        try:
            resp = self.get(url)
        except Exception:
            return out
        soup = BeautifulSoup(resp.text, "lxml")
        targets: list[str] = []
        for tr in soup.find_all("tr"):
            cells = tr.find_all(["th", "td"])
            if len(cells) < 2:
                continue
            label = cells[0].get_text(strip=True)
            val = _trim(cells[1].get_text(" ", strip=True))
            if not val or val == "明記なし" or val == "なし":
                continue
            if "deadline_note" not in out and any(k in label for k in _DEADLINE_LABELS):
                out["deadline_note"] = val
            elif "amount" not in out and any(k in label for k in _AMOUNT_LABELS):
                out["amount"] = val
            elif "official_url" not in out and any(k in label for k in _OFFICIAL_LABELS):
                a = cells[1].find("a")
                href = a.get("href") if a else val
                if href and href.startswith("http"):
                    out["official_url"] = href
            elif any(k in label for k in _TARGET_LABELS):
                targets.append(f"{label}: {val}")
        if targets:
            raw = " / ".join(targets[:3])
            out["target"] = extract_tags(raw, include_destination=True) or _trim(raw, 200)
        return out
