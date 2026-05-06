import time
from dataclasses import dataclass
from datetime import date
from typing import Iterable

import feedparser
import requests

from .. import config


@dataclass
class ScholarshipItem:
    external_id: str
    title: str
    url: str  # アグリゲータの解説ページURL（出典として使う）
    deadline: date | None
    region: str  # 'domestic' or 'overseas'
    deadline_note: str | None = None  # 「例年2月末日」のような曖昧な傾向表記
    amount: str | None = None          # 額面（例：「月額12万円」「全額(上限$50,000)」）
    target: str | None = None          # 対象（例：「修士1〜2年生／BME分野」）
    scholarship_type: str | None = None  # 「給付型」「貸与型」など
    official_url: str | None = None      # 財団・奨学金の公式サイトURL


class Scraper:
    source_id: str = ""
    source_label: str = ""
    region: str = ""

    def fetch(self) -> Iterable[ScholarshipItem]:
        raise NotImplementedError

    def enrich(self, item: ScholarshipItem) -> ScholarshipItem:
        """個別ページから公式URL等を追加で取得（新規追加分にのみ呼ぶ）。

        デフォルトでは何もしない。サブクラスでオーバーライド。
        """
        return item

    def get(self, url: str) -> requests.Response:
        time.sleep(config.REQUEST_INTERVAL_SEC)
        resp = requests.get(
            url,
            headers={"User-Agent": config.USER_AGENT},
            timeout=30,
        )
        resp.raise_for_status()
        return resp

    def parse_feed(self, url: str):
        """Fetch via requests (avoids feedparser's urllib SSL issues) and parse."""
        resp = requests.get(
            url,
            headers={"User-Agent": config.USER_AGENT, "Cache-Control": "no-cache"},
            timeout=30,
        )
        resp.raise_for_status()
        return feedparser.parse(resp.content)
