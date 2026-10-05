# Validation record

Latest review: 2026-10-05 (UTC). Previous review: 2026-09-22.

## Live end-to-end run, 2026-10-05

All steps ran in a Linux container with Python 3.11, against live TMDB data and a real PostgreSQL database. The TMDB key came from the environment and was not committed.

| Step | Command | Result |
|---|---|---|
| Database | `docker compose up -d` (`postgres:17`) | Container started; `pg_isready` accepted connections. |
| Dependencies | `pip install -r requirements.txt` | dlt 1.30.0, dbt-core 1.12.5, dbt-postgres 1.11.0, pandas 3.0.6, Streamlit 1.65.0, Plotly 7.1.0. |
| Ingestion | `python pipeline.py` (default `.env.example` settings: 5 pages, `revenue.desc`, `vote_count.gte=50`) | Load package `LOADED` with no failed jobs in about 52 s. `raw.movies` = 100 rows, `raw.genres` = 19 rows. The source-response checks raised no errors. |
| dbt connection | `dbt debug --profiles-dir .` | All checks passed. |
| dbt models | `dbt run --profiles-dir .` | 2 of 2 OK: `analytics.stg_movies` (view, 100 rows) and `analytics.genre_decade_summary` (table, 42 rows). |
| dbt tests | `dbt test --profiles-dir .` | 11 of 11 PASS: 7 schema tests and 4 singular tests. |
| Dashboard | `streamlit run app/streamlit_app.py` | Rendered with no load errors. KPIs under default filters: 100 movies loaded, average rating 7.31, highest grossing *Avengers: Endgame* at $2,925,499,985. |
| Screenshot | Headless Chromium (Playwright) on the running app | Saved as `docs/dashboard-preview.png`. It replaces the earlier illustrative SVG. |

Cross-checks run directly against PostgreSQL:

- No rows in `raw.movies` have a non-positive budget or revenue. The staging filters removed 0 of 100 movies.
- The bars in the dashboard's genre ROI chart match a SQL aggregation of `stg_movies` × `raw.genres`. For example, Animation has 26 movies with an average ROI of 8.69, and Action has 52 movies with an average ROI of 6.25.
- The README's snapshot tables come from these same queries.

This is one run. TMDB data and rankings change over time, so a rerun will give different figures.

## CI and regression checks

- `make check` passed: ruff lint, the evidence and syntax check, and the Python regression tests covering filter-aware aggregation, duplicate handling, the empty-input schema and environment parsing.
- CI (`.github/workflows/evidence.yml`) runs the same checks on every pull request. CI has no TMDB key or database, so it does not repeat the live run.

## Not completed

- No persistent hosted dashboard deployment was validated.
- No incremental or scheduled ingestion was tested. Each run replaces the previous snapshot.
