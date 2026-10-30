"""Extract TMDB movie data and load it into PostgreSQL with dlt."""

import json
import os
import time
from collections.abc import Callable, Iterable
from datetime import datetime, timezone
from typing import Any

import dlt
import requests
from dotenv import load_dotenv

from movie_analytics.config import configure_dlt_postgres_from_env
from movie_analytics.contracts import discovery_results, movie_details
from movie_analytics.sampling import Sampling


TMDB_BASE_URL = "https://api.themoviedb.org/3"

Fetch = Callable[[str, str, dict[str, Any] | None], dict[str, Any]]


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
def genres(api_key: str, fetch: Fetch = tmdb_get) -> Iterable[dict[str, Any]]:
    """Yield the TMDB movie-genre lookup table."""
    payload = fetch("/genre/movie/list", api_key)
    ingested_at = datetime.now(timezone.utc).isoformat()

    for genre in payload.get("genres", []):
        yield {
            "id": genre["id"],
            "name": genre["name"],
            "source": "tmdb.genre.movie.list",
            "ingested_at": ingested_at,
        }


@dlt.resource(name="movies", write_disposition="replace", primary_key="id")
def movies(
    api_key: str, fetch: Fetch = tmdb_get, pause_seconds: float = 0.05
) -> Iterable[dict[str, Any]]:
    """Yield enriched movie records from TMDB discovery and detail endpoints."""
    sampling = Sampling.from_env()
    ingested_at = datetime.now(timezone.utc).isoformat()
    seen_ids: set[int] = set()

    for request in sampling.requests():
        discover_payload = fetch("/discover/movie", api_key, request)

        for item in discovery_results(discover_payload, request["page"]):
            movie_id = item.get("id")
            if not movie_id or movie_id in seen_ids:
                continue
            seen_ids.add(movie_id)

            details = movie_details(fetch(f"/movie/{movie_id}", api_key), movie_id)
            time.sleep(pause_seconds)

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
                "sampling": sampling.profile,
                "source": "tmdb.discover.movie+tmdb.movie.details",
                "ingested_at": ingested_at,
            }


def run_pipeline(api_key: str, fetch: Fetch = tmdb_get, pause_seconds: float = 0.05):
    """Load genres and movies into the raw schema and return dlt's load info."""
    configure_dlt_postgres_from_env()
    pipeline = dlt.pipeline(
        pipeline_name="tmdb_movie_analytics",
        destination="postgres",
        dataset_name="raw",
    )
    return pipeline.run([genres(api_key, fetch), movies(api_key, fetch, pause_seconds)])


def main() -> None:
    """Run the TMDB-to-PostgreSQL ingestion pipeline."""
    load_dotenv()
    api_key = os.getenv("TMDB_API_KEY")
    if not api_key:
        raise RuntimeError(
            "TMDB_API_KEY is required. Copy .env.example to .env and add your key."
        )

    print(run_pipeline(api_key))


if __name__ == "__main__":
    main()
