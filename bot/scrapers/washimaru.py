from typing import Iterable

from .base import Scraper, ScholarshipItem


class Washimaru(Scraper):
    source_id = "washimaru"
    source_label = "わしまる大学"
    region = "domestic"
    feed_url = "https://washimaru-univ.com/category/money/scholarship/feed/"

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
                region=self.region,
            )
