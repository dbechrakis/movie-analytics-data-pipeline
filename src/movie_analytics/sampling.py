"""Which TMDB discovery requests build the sample, as plain data with no network or dlt."""

from collections.abc import Iterator
from dataclasses import dataclass
import os

from movie_analytics.config import env_int


PROFILES = ("revenue", "stratified_year")


@dataclass(frozen=True)
class Sampling:
    """Settings that decide which films enter the raw layer.

    revenue: the highest-grossing films overall. Ranking by revenue selects on the outcome that
    the ROI proxy divides by budget, so it inflates ROI.
    stratified_year: the most-voted films of each release year. Votes measure exposure, not
    revenue, and every year contributes the same number of pages.
    """

    profile: str = "revenue"
    max_pages: int = 5
    vote_count_gte: int = 50
    sort_by: str = "revenue.desc"
    year_from: int = 2005
    year_to: int = 2025
    pages_per_year: int = 1

    def __post_init__(self):
        if self.profile not in PROFILES:
            raise ValueError(f"TMDB_SAMPLING must be one of {PROFILES}, got {self.profile!r}")
        if self.max_pages < 1 or self.pages_per_year < 1:
            raise ValueError("Page counts must be at least 1")
        if self.year_from > self.year_to:
            raise ValueError("TMDB_YEAR_FROM must not be after TMDB_YEAR_TO")

    @classmethod
    def from_env(cls) -> "Sampling":
        return cls(
            profile=os.getenv("TMDB_SAMPLING") or "revenue",
            max_pages=env_int("TMDB_MAX_PAGES", 5),
            vote_count_gte=env_int("TMDB_VOTE_COUNT_GTE", 50),
            sort_by=os.getenv("TMDB_DISCOVER_SORT_BY") or "revenue.desc",
            year_from=env_int("TMDB_YEAR_FROM", 2005),
            year_to=env_int("TMDB_YEAR_TO", 2025),
            pages_per_year=env_int("TMDB_PAGES_PER_YEAR", 1),
        )

    def requests(self) -> Iterator[dict]:
        """Yield the parameters of every discovery request, in order."""
        base = {"vote_count.gte": self.vote_count_gte, "include_adult": "false",
                "include_video": "false"}
        if self.profile == "revenue":
            for page in range(1, self.max_pages + 1):
                yield {**base, "page": page, "sort_by": self.sort_by}
            return
        for year in range(self.year_from, self.year_to + 1):
            for page in range(1, self.pages_per_year + 1):
                yield {**base, "page": page, "sort_by": "vote_count.desc",
                       "primary_release_year": year}
