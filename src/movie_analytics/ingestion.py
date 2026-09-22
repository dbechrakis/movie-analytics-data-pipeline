"""Extract TMDB movie data and load it into PostgreSQL with dlt."""

import json
import os
import time
from collections.abc import Iterable
from datetime import datetime, timezone
from typing import Any

import dlt
import requests
from dotenv import load_dotenv

from movie_analytics.config import configure_dlt_postgres_from_env, env_int


TMDB_BASE_URL = "https://api.themoviedb.org/3"


def tmdb_get(
    path: str,
    api_key: str,
    params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Request one TMDB endpoint and return its decoded JSON payload."""
    request_params = {"api_key": api_key}
    if params:
        request_params.update(params)

    response = requests.get(
        f"{TMDB_BASE_URL}{path}",
        params=request_params,
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


@dlt.resource(name="genres", write_disposition="replace", primary_key="id")
def genres(api_key: str) -> Iterable[dict[str, Any]]:
    """Yield the TMDB movie-genre lookup table."""
    payload = tmdb_get("/genre/movie/list", api_key)
    ingested_at = datetime.now(timezone.utc).isoformat()

    for genre in payload.get("genres", []):
        yield {
            "id": genre["id"],
            "name": genre["name"],
            "source": "tmdb.genre.movie.list",
            "ingested_at": ingested_at,
        }


@dlt.resource(name="movies", write_disposition="replace", primary_key="id")
def movies(api_key: str) -> Iterable[dict[str, Any]]:
    """Yield enriched movie records from TMDB discovery and detail endpoints."""
    max_pages = env_int("TMDB_MAX_PAGES", 5)
    vote_count_gte = env_int("TMDB_VOTE_COUNT_GTE", 50)
    sort_by = os.getenv("TMDB_DISCOVER_SORT_BY", "revenue.desc")
    ingested_at = datetime.now(timezone.utc).isoformat()
    seen_ids: set[int] = set()

    for page in range(1, max_pages + 1):
        discover_payload = tmdb_get(
            "/discover/movie",
            api_key,
            {
                "page": page,
                "sort_by": sort_by,
                "vote_count.gte": vote_count_gte,
                "include_adult": "false",
                "include_video": "false",
            },
        )

        for item in discover_payload.get("results", []):
            movie_id = item.get("id")
            if not movie_id or movie_id in seen_ids:
                continue
            seen_ids.add(movie_id)

            details = tmdb_get(f"/movie/{movie_id}", api_key)
            time.sleep(0.05)

            genre_ids = [
                genre["id"]
                for genre in details.get("genres", [])
                if genre.get("id") is not None
            ]

            yield {
                "id": details.get("id"),
                "title": details.get("title") or details.get("original_title"),
                "release_date": details.get("release_date"),
                "genre_ids": json.dumps(genre_ids),
                "budget": details.get("budget"),
                "revenue": details.get("revenue"),
                "vote_average": details.get("vote_average"),
                "vote_count": details.get("vote_count"),
                "popularity": details.get("popularity"),
                "source": "tmdb.discover.movie+tmdb.movie.details",
                "ingested_at": ingested_at,
            }


def main() -> None:
    """Run the TMDB-to-PostgreSQL ingestion pipeline."""
    load_dotenv()
    api_key = os.getenv("TMDB_API_KEY")
    if not api_key:
        raise RuntimeError(
            "TMDB_API_KEY is required. Copy .env.example to .env and add your key."
        )

    configure_dlt_postgres_from_env()
    pipeline = dlt.pipeline(
        pipeline_name="tmdb_movie_analytics",
        destination="postgres",
        dataset_name="raw",
    )
    info = pipeline.run([genres(api_key), movies(api_key)])
    print(info)


if __name__ == "__main__":
    main()
