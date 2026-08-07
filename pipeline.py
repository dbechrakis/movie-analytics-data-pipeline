import json
import os
import time
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List

import dlt
import requests
from dotenv import load_dotenv


TMDB_BASE_URL = "https://api.themoviedb.org/3"


def env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None or value.strip() == "":
        return default
    return int(value)


def tmdb_get(path: str, api_key: str, params: Dict[str, Any] | None = None) -> Dict[str, Any]:
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
def genres(api_key: str) -> Iterable[Dict[str, Any]]:
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
def movies(api_key: str) -> Iterable[Dict[str, Any]]:
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

            details = tmdb_get("/movie/{movie_id}".format(movie_id=movie_id), api_key)
            time.sleep(0.05)

            genre_ids: List[int] = [
                genre["id"] for genre in details.get("genres", []) if genre.get("id") is not None
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


def configure_dlt_postgres_from_env() -> None:
    mappings = {
        "DESTINATION__POSTGRES__CREDENTIALS__HOST": "POSTGRES_HOST",
        "DESTINATION__POSTGRES__CREDENTIALS__PORT": "POSTGRES_PORT",
        "DESTINATION__POSTGRES__CREDENTIALS__DATABASE": "POSTGRES_DB",
        "DESTINATION__POSTGRES__CREDENTIALS__USERNAME": "POSTGRES_USER",
        "DESTINATION__POSTGRES__CREDENTIALS__PASSWORD": "POSTGRES_PASSWORD",
    }
    defaults = {
        "POSTGRES_HOST": "localhost",
        "POSTGRES_PORT": "5432",
        "POSTGRES_DB": "movies",
        "POSTGRES_USER": "itc6050",
        "POSTGRES_PASSWORD": "itc6050",
    }

    for dlt_key, app_key in mappings.items():
        os.environ.setdefault(dlt_key, os.getenv(app_key, defaults[app_key]))


def main() -> None:
    load_dotenv()
    api_key = os.getenv("TMDB_API_KEY")
    if not api_key:
        raise RuntimeError("TMDB_API_KEY is required. Copy .env.example to .env and add your key.")

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
