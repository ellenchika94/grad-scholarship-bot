from typing import Iterable

from .base import Scraper, ScholarshipItem


class Xplane(Scraper):
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
                region=self.region,
            )
