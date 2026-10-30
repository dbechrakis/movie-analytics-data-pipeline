"""Synthetic stand-in for the TMDB API, used only to test the pipeline without a key.

Every film is invented. Titles start with "Synthetic Film" so the rows cannot be mistaken for
real data, and nothing computed from them is a finding.
"""

import math
import random

GENRES = [{"id": 18, "name": "Drama"}, {"id": 35, "name": "Comedy"}, {"id": 28, "name": "Action"},
          {"id": 16, "name": "Animation"}, {"id": 878, "name": "Science Fiction"}]
YEARS = range(1995, 2026)
FILMS_PER_YEAR = 60
PAGE_SIZE = 20
MISSING_FINANCIALS_SHARE = 0.15


def _film(year: int, index: int) -> dict:
    rng = random.Random(year * 1000 + index)
    movie_id = year * 100 + index
    votes = int(math.exp(rng.gauss(6.5, 1.5)))
    budget = 0 if rng.random() < MISSING_FINANCIALS_SHARE else int(math.exp(rng.gauss(17.0, 1.2)))
    revenue = 0 if budget == 0 else int(budget * math.exp(rng.gauss(0.9, 1.1)))
    genre_ids = rng.sample([g["id"] for g in GENRES], rng.randint(1, 3))
    return {
        "id": movie_id, "title": f"Synthetic Film {movie_id}",
        "release_date": f"{year}-{rng.randint(1, 12):02d}-{rng.randint(1, 28):02d}",
        "genres": [g for g in GENRES if g["id"] in genre_ids],
        "budget": budget, "revenue": revenue, "vote_count": votes,
        "vote_average": round(rng.uniform(4.0, 9.0), 1), "popularity": round(rng.uniform(1, 200), 2),
    }


UNIVERSE = [_film(year, i) for year in YEARS for i in range(FILMS_PER_YEAR)]
BY_ID = {film["id"]: film for film in UNIVERSE}


def fake_get(path: str, api_key: str, params: dict | None = None) -> dict:
    """Answer the three TMDB endpoints the pipeline uses."""
    params = params or {}
    if path == "/genre/movie/list":
        return {"genres": GENRES}
    if path == "/discover/movie":
        films = [f for f in UNIVERSE if f["vote_count"] >= int(params.get("vote_count.gte", 0))]
        if "primary_release_year" in params:
            films = [f for f in films if f["release_date"].startswith(str(params["primary_release_year"]))]
        sort_key, _, _ = params["sort_by"].partition(".")
        films.sort(key=lambda f: f[sort_key], reverse=True)
        start = (int(params["page"]) - 1) * PAGE_SIZE
        return {"page": int(params["page"]), "results": films[start:start + PAGE_SIZE]}
    if path.startswith("/movie/"):
        return BY_ID[int(path.rsplit("/", 1)[1])]
    raise ValueError(f"Unexpected path {path}")
