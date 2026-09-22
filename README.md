# Movie Industry Analytics Data Product

[![Evidence checks](https://github.com/dbechrakis/movie-analytics-data-pipeline/actions/workflows/evidence.yml/badge.svg)](https://github.com/dbechrakis/movie-analytics-data-pipeline/actions/workflows/evidence.yml)

An end-to-end analytics product that turns TMDB API data into tested analytical models and an interactive decision dashboard.

**Stack:** Python · dlt · PostgreSQL · dbt · Streamlit · Plotly · Docker

![Dashboard preview](docs/dashboard-preview.svg)

## Business problem

Movie-performance analysis is often built directly on raw API responses, which makes metric definitions, filtering, and repeated analysis inconsistent. This project creates a reproducible path from source data to business-facing analysis so users can investigate:

- which genres show the strongest average gross ROI proxy;
- how ratings vary across release periods;
- how reported production budget relates to reported revenue;
- how conclusions change across genres, decades, and vote-count thresholds.

The product is designed for exploratory decision support, not for claiming causal investment recommendations.

## Solution overview

The system separates ingestion, transformation, testing, and presentation into explicit layers:

```mermaid
flowchart LR
    A["TMDB API"] --> B["dlt ingestion"]
    B --> C["PostgreSQL raw layer"]
    C --> D["dbt staging + tests"]
    D --> E["Analytics mart"]
    E --> F["Streamlit dashboard"]
```

| Layer | Responsibility | Main output |
|---|---|---|
| Ingestion | Extract discovery, movie-detail, and genre data | `raw.movies`, `raw.genres` |
| Staging | Type, clean, filter, and derive movie-level fields | `analytics.stg_movies` |
| Analytics | Aggregate genre × decade performance | `analytics.genre_decade_summary` |
| Quality | Enforce schema and business-rule checks | dbt + Python test results |
| Presentation | Apply consistent filters and surface KPIs/charts | Interactive Streamlit dashboard |

See the [architecture notes](docs/architecture.md) for component boundaries and data contracts.

## Data and metric definitions

The default ingestion requests five TMDB discovery pages sorted by reported revenue and requires at least 50 votes before retrieving movie details. The dbt staging layer then keeps records with:

- a valid title and release date;
- positive reported budget and revenue;
- a rating between 0 and 10.

The key derived metric is:

```text
Gross ROI proxy = (reported revenue - reported production budget) / reported production budget
```

This is **not net investor return**. It excludes marketing, distribution, financing, taxes, and exhibitor revenue sharing. Movies may belong to multiple genres, so genre counts must not be added together as if they were mutually exclusive.

## Data quality and validation

Quality controls exist at three levels:

1. **dbt schema tests** check identifiers, required fields, and movie-grain uniqueness.
2. **dbt singular tests** reject impossible ratings, non-positive financial values, empty marts, and invalid ROI values.
3. **Python regression tests** verify filtered-summary behavior, duplicate handling, empty inputs, and environment parsing.

CI validates committed Python syntax and runs the regression suite on every pull request and push to `main`. The exact rerun scope is recorded in [VALIDATION.md](VALIDATION.md); the repository does not represent synthetic tests as a live TMDB/database validation.

## Dashboard output

The Streamlit interface provides:

- movie-count, average-rating, and highest-grossing KPIs;
- genre ranking by average gross ROI proxy;
- average-rating trends by release year;
- budget-versus-revenue exploration on logarithmic scales;
- genre, decade, and minimum-vote filters;
- a filtered genre × decade summary table.

All visible summaries use the active dashboard filters. Metrics that require movie grain deduplicate movies after filtering, preventing multi-genre rows from inflating movie-level KPIs.

## Repository structure

```text
movie-analytics-data-pipeline/
├── app/                        # Streamlit deployment entry point
├── dbt/                        # Staging models, mart, tests, and profile
├── docs/                       # Architecture and dashboard preview
├── src/movie_analytics/        # Reusable Python package
│   ├── config.py               # Environment configuration
│   ├── ingestion.py            # TMDB → PostgreSQL pipeline
│   ├── metrics.py              # Filter-aware business metrics
│   └── dashboard.py            # Dashboard data access and UI
├── tests/                      # Python regression tests
├── ci/                         # Evidence and syntax validation
├── dashboard.py               # Backward-compatible UI entry point
├── pipeline.py                # Backward-compatible ingestion entry point
├── docker-compose.yml         # Local PostgreSQL service
├── pyproject.toml             # Package metadata
└── requirements.txt           # Runtime dependencies
```

## Run locally

### 1. Create the environment

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
cp .env.example .env
```

Add a TMDB API key to `.env`. Never commit `.env` or real credentials.

### 2. Start PostgreSQL

```bash
docker compose up -d
```

### 3. Ingest TMDB data

```bash
python pipeline.py
```

### 4. Build and test the analytics layer

```bash
cd dbt
dbt debug --profiles-dir .
dbt run --profiles-dir .
dbt test --profiles-dir .
cd ..
```

### 5. Launch the dashboard

```bash
streamlit run app/streamlit_app.py
```

The previous command, `streamlit run dashboard.py`, remains supported.

### 6. Run Python tests

```bash
python -m unittest discover -s tests -v
```

## Design decisions and limitations

- **Selected sample:** revenue-ranked TMDB discovery pages are not representative of the film industry.
- **Reported financials:** missing or inaccurate TMDB budget/revenue values can bias results.
- **Descriptive analysis:** associations in the dashboard are not causal effects.
- **Replace loading:** the portfolio-scale ingestion favors reproducibility over incremental history.
- **Local credentials:** defaults support local Docker use only; production secrets require a proper secret manager.

## Future improvements

- Add incremental ingestion with freshness and volume monitoring.
- Introduce orchestration only when scheduled execution is required.
- Add a small deployment dataset or hosted database for a persistent public demo.
- Extend the mart with profitability bands and minimum-sample guardrails for rankings.

## Context and ownership

Portfolio case study developed from MSc Data Science coursework at **The American College of Greece** and refactored into a professional analytics-product structure. The academic origin is retained for transparency. See [LICENSING.md](LICENSING.md) for the repository's licensing scope.

**Dimitris Bechrakis**

Business Analyst | Commercial Analytics · Data Products · Applied Data Science
