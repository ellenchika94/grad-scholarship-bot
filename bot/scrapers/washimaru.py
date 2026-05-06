import re
from datetime import date
from typing import Iterable

from bs4 import BeautifulSoup

from .base import Scraper, ScholarshipItem
from .tagging import extract_tags


_DEADLINE_RE = re.compile(
    r"締め?切[りもの]?[:：]?\s*"
    r"(?P<y>\d{4})年\s*(?P<m>\d{1,2})月\s*"
    r"(?:(?P<d>\d{1,2})日|(?P<rough>上旬|中旬|下旬))"
)
_ROUGH_TO_DAY = {"上旬": 5, "中旬": 15, "下旬": 25}


def _parse_deadline(text: str) -> date | None:
    m = _DEADLINE_RE.search(text)
    if not m:
        return None
    y = int(m.group("y"))
    mon = int(m.group("m"))
    if m.group("d"):
        d = int(m.group("d"))
    else:
        d = _ROUGH_TO_DAY.get(m.group("rough"), 15)
    try:
        return date(y, mon, d)
    except ValueError:
        return None


class Washimaru(Scraper):
    """わしまる大学の修士向け給付型奨学金一覧をスクレイピング。

    一覧ページ自体がキュレーションされたアグリゲータなので、ブログRSSではなく
    ここを直接読む（ブログRSSはガイド記事も混ざるため不適）。
    """

    source_id = "washimaru"
    source_label = "わしまる大学"
    region = "domestic"
    list_url = "https://washimaru-univ.com/minkankyufu-m/"

    def fetch(self) -> Iterable[ScholarshipItem]:
        resp = self.get(self.list_url)
        soup = BeautifulSoup(resp.text, "lxml")
        seen_urls: set[str] = set()
        for box in soup.select("div.wp-block-jin-gb-block-box-with-headline.kaisetsu-box2"):
            link = box.select_one('a[href*="scholarship-pickup"]')
            if not link:
                continue
            url = link.get("href", "").strip()
            if not url or url in seen_urls:
                continue
            seen_urls.add(url)

            title = self._find_title(box)
            if not title:
                continue

            fields = self._parse_box_fields(box)

            target_raw = fields.get("target")
            deadline_text = fields.get("deadline_text", "")
            # 「上旬/中旬/下旬」表記の場合は原文を deadline_note に残す
            note = None
            if deadline_text and re.search(r"上旬|中旬|下旬", deadline_text):
                note = deadline_text.replace("締め切り：", "").replace("締切：", "").strip()
            # /minkankyufu-m/ は修士向けキュレーションなので、タグに修士が無ければ補う
            tags = extract_tags(target_raw)
            if tags and "修士" not in tags:
                tags = "修士 / " + tags
            elif not tags:
                tags = "修士"
            yield ScholarshipItem(
                external_id=url,
                title=title,
                url=url,
                deadline=_parse_deadline(deadline_text),
                deadline_note=note,
                region=self.region,
                amount=fields.get("amount"),
                target=tags,
                scholarship_type="給付型",  # /minkankyufu-m/ は給付型限定のページ
            )

    def enrich(self, item: ScholarshipItem) -> ScholarshipItem:
        """個別pickupページから公式財団URLを取得。"""
        try:
            resp = self.get(item.url)
        except Exception:
            return item
        soup = BeautifulSoup(resp.text, "lxml")
        for a in soup.select("article a[href]"):
            href = a.get("href", "")
            text = a.get_text(strip=True)
            if not href.startswith("http") or "washimaru" in href:
                continue
            if "公式" in text or "財団HP" in text or "公式HP" in text:
                item.official_url = href
                break
        return item

    @staticmethod
    def _parse_box_fields(box) -> dict[str, str]:
        result: dict[str, str] = {}
        for li in box.select("li"):
            text = li.get_text(strip=True)
            if "締め切り" in text or "締切" in text:
                result["deadline_text"] = text
            elif text.startswith("受給月額") or text.startswith("受給額"):
                result["amount"] = text.split("：", 1)[-1].strip() if "：" in text else text
            elif text.startswith("応募可能学年") or text.startswith("学部制限"):
                val = text.split("：", 1)[-1].strip() if "：" in text else text
                result["target"] = (result.get("target", "") + " / " + val).strip(" /")
        return result

    @staticmethod
    def _find_title(box) -> str:
        prev = box
        for _ in range(10):
            prev = prev.previous_sibling
            if prev is None:
                break
            if getattr(prev, "name", None) in ("h2", "h3", "h4", "h5"):
                return prev.get_text(strip=True)
        return ""
