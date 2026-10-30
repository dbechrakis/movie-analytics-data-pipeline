"""Write a dated JSON summary of the transformed layer, with the figures that qualify the sample."""

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
from typing import Any

from sqlalchemy import URL, create_engine, text


GENRE_MIN_MOVIES = 10

SUMMARY_SQL = """
select
    (select count(*) from raw.movies) as ingested,
    count(*) as kept,
    min(sampling) as sampling,
    count(distinct sampling) as sampling_values,
    min(release_year) as first_year,
    max(release_year) as last_year,
    min(vote_count) as min_vote_count,
    avg(vote_average) as avg_rating,
    avg(roi) as mean_roi,
    percentile_cont(0.5) within group (order by roi) as median_roi,
    sum(revenue) as total_revenue,
    min(revenue) as min_revenue
from analytics.stg_movies
"""

GENRE_SQL = """
select
    g.name as genre,
    count(distinct m.movie_id) as movies,
    avg(m.roi) as mean_roi,
    percentile_cont(0.5) within group (order by m.roi) as median_roi,
    avg(m.vote_average) as avg_rating
from analytics.stg_movies m
cross join lateral jsonb_array_elements_text(m.genre_ids::jsonb) as expanded(genre_id)
join raw.genres g on g.id = expanded.genre_id::bigint
group by g.name
having count(distinct m.movie_id) >= :minimum
order by mean_roi desc
"""


def database_url() -> URL:
    return URL.create(
        drivername="postgresql+psycopg2",
        username=os.getenv("POSTGRES_USER", "itc6050"),
        password=os.getenv("POSTGRES_PASSWORD", "itc6050"),
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=int(os.getenv("POSTGRES_PORT", "5432")),
        database=os.getenv("POSTGRES_DB", "movies"),
    )


def dbt_test_counts(run_results: Path) -> dict[str, int] | None:
    """Pass and total counts from dbt's run_results.json, or None when it is missing."""
    if not run_results.exists():
        return None
    results = json.loads(run_results.read_text())["results"]
    return {"passed": sum(r["status"] == "pass" for r in results), "total": len(results)}


def rounded(value: Any, digits: int = 4) -> Any:
    return round(float(value), digits) if value is not None else None


def build_snapshot(engine, dbt_results: Path | None = None) -> dict:
    with engine.connect() as connection:
        summary = connection.execute(text(SUMMARY_SQL)).mappings().one()
        genres = connection.execute(text(GENRE_SQL), {"minimum": GENRE_MIN_MOVIES}).mappings().all()
    if summary["kept"] == 0:
        raise ValueError("The transformed layer is empty, so there is nothing to summarise")
    if summary["sampling_values"] != 1:
        raise ValueError("The transformed layer mixes sampling profiles")
    ingested, kept = int(summary["ingested"]), int(summary["kept"])
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "sampling": summary["sampling"],
        "movies_ingested": ingested,
        "movies_after_staging_filters": kept,
        "share_dropped_by_staging_filters": rounded(1 - kept / ingested),
        "release_years": [int(summary["first_year"]), int(summary["last_year"])],
        "min_vote_count": int(summary["min_vote_count"]),
        "min_revenue": rounded(summary["min_revenue"], 0),
        "avg_rating": rounded(summary["avg_rating"], 2),
        "roi_mean": rounded(summary["mean_roi"]),
        "roi_median": rounded(summary["median_roi"]),
        "total_revenue": rounded(summary["total_revenue"], 0),
        "genres_with_at_least_10_movies": [
            {"genre": g["genre"], "movies": int(g["movies"]), "roi_mean": rounded(g["mean_roi"], 2),
             "roi_median": rounded(g["median_roi"], 2), "avg_rating": rounded(g["avg_rating"], 2)}
            for g in genres
        ],
        "dbt_tests": dbt_test_counts(dbt_results) if dbt_results else None,
    }


def main(argv=None) -> Path:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=Path("snapshots"))
    parser.add_argument("--dbt-results", type=Path, default=Path("dbt/target/run_results.json"))
    args = parser.parse_args(argv)
    snapshot = build_snapshot(create_engine(database_url()), args.dbt_results)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    stamp = snapshot["generated_at"][:10]
    path = args.output_dir / f"{stamp}_{snapshot['sampling']}.json"
    path.write_text(json.dumps(snapshot, indent=2) + "\n")
    print(path)
    return path


if __name__ == "__main__":
    main()
