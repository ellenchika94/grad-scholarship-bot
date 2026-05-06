import re
from datetime import date
from typing import Iterable

from bs4 import BeautifulSoup

from .base import Scraper, ScholarshipItem


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

            deadline_text = ""
            for li in box.select("li"):
                t = li.get_text(strip=True)
                if "締め切り" in t or "締切" in t:
                    deadline_text = t
                    break

            yield ScholarshipItem(
                external_id=url,
                title=title,
                url=url,
                deadline=_parse_deadline(deadline_text),
                region=self.region,
            )

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
