"""Run ingestion, dbt, the snapshot and the dashboard against a synthetic TMDB, for both profiles.

This needs a PostgreSQL database and no TMDB key. It proves the pipeline works end to end. The films
are invented, so nothing it computes is a finding.
"""

import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "ci"))

import streamlit as st  # noqa: E402
from sqlalchemy import create_engine, text  # noqa: E402
from streamlit.testing.v1 import AppTest  # noqa: E402

from fake_tmdb import fake_get  # noqa: E402
from movie_analytics import snapshot  # noqa: E402
from movie_analytics.dashboard import SAMPLE_NOTICES  # noqa: E402
from movie_analytics.ingestion import run_pipeline  # noqa: E402

PROFILES = {
    "revenue": {"TMDB_MAX_PAGES": "2", "expected": 40},
    "stratified_year": {"TMDB_YEAR_FROM": "2015", "TMDB_YEAR_TO": "2018", "TMDB_PAGES_PER_YEAR": "1",
                        "expected": 80},
}


def dbt(*arguments):
    result = subprocess.run(["dbt", *arguments, "--profiles-dir", "."], cwd=ROOT / "dbt",
                            capture_output=True, text=True)
    if result.returncode != 0:
        print(result.stdout[-3000:], result.stderr[-1000:])
        raise SystemExit(f"dbt {arguments[0]} failed")


def scalar(engine, sql):
    with engine.connect() as connection:
        return connection.execute(text(sql)).scalar_one()


def check(profile, settings):
    expected = int(settings.pop("expected"))
    os.environ.update({"TMDB_SAMPLING": profile, **settings})
    run_pipeline("synthetic", fake_get, pause_seconds=0)
    dbt("run")
    dbt("test")
    engine = create_engine(snapshot.database_url())
    raw = scalar(engine, "select count(*) from raw.movies")
    kept = scalar(engine, "select count(*) from analytics.stg_movies")
    assert raw == expected, (profile, raw, expected)
    assert 0 < kept <= raw, (profile, kept, raw)
    if profile == "stratified_year":
        assert kept < raw, f"films without budget or revenue should be dropped, kept {kept} of {raw}"
    else:
        assert kept == raw, f"revenue ranking should keep films that all report revenue, kept {kept} of {raw}"
    assert scalar(engine, "select count(distinct sampling) from raw.movies") == 1
    assert scalar(engine, "select min(sampling) from raw.movies") == profile
    assert scalar(engine, "select count(*) from analytics.genre_decade_summary") > 0

    result = snapshot.build_snapshot(engine, ROOT / "dbt" / "target" / "run_results.json")
    assert result["sampling"] == profile
    assert (result["movies_ingested"], result["movies_after_staging_filters"]) == (raw, kept)
    assert result["dbt_tests"]["passed"] == result["dbt_tests"]["total"] > 0
    json.dumps(result)

    st.cache_data.clear()
    page = AppTest.from_file(str(ROOT / "app" / "streamlit_app.py"), default_timeout=90).run()
    assert not page.exception, page.exception
    assert page.info and SAMPLE_NOTICES[profile] in page.info[0].value
    print(f"{profile}: ingested {raw}, kept {kept}, dashboard rendered with the matching notice")


def main():
    for profile, settings in PROFILES.items():
        check(profile, dict(settings))
    print("Pipeline check passed on synthetic data.")


if __name__ == "__main__":
    main()
