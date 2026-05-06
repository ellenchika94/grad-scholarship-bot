from .base import Scraper, ScholarshipItem
from .washimaru import Washimaru
from .xplane import Xplane

ALL_SCRAPERS: list[Scraper] = [
    Washimaru(),
    Xplane(),
]

__all__ = ["Scraper", "ScholarshipItem", "ALL_SCRAPERS"]
