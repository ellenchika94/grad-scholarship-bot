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
    url: str
    deadline: date | None
    region: str  # 'domestic' or 'overseas'


class Scraper:
    source_id: str = ""
    source_label: str = ""
    region: str = ""

    def fetch(self) -> Iterable[ScholarshipItem]:
        raise NotImplementedError

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
