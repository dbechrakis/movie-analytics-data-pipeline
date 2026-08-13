# Movie Industry Analytics — Data Pipeline & Decision Dashboard

An end-to-end analytics case study that turns **TMDB movie data into an analytical mart and interactive decision dashboard** using dlt, PostgreSQL, dbt, Python, and Streamlit.

## Executive summary

The project builds a complete path from external API data to business-facing analytics:

**TMDB API → dlt ingestion → PostgreSQL → dbt transformations → Streamlit dashboard**

The dashboard explores movie performance through **ROI, ratings, release periods, genres, budgets, and revenue**, with filters that allow users to investigate different segments.

## What this demonstrates

- **Data ingestion:** API-based extraction and structured loading
- **Data engineering:** PostgreSQL storage and transformation layers
- **Analytics engineering:** dbt staging and analytical mart
- **Business analytics:** ROI, ratings, revenue, genre and decade analysis
- **Decision support:** interactive KPIs, filters and visual exploration

## Dashboard

The Streamlit application provides:

- KPI overview of the movie dataset
- Top genres by average ROI
- Average rating trends by release year
- Budget vs revenue analysis
- Genre and decade filtering
- Analytical summary data from the dbt mart

The purpose is not simply to display charts, but to create a reproducible workflow from **raw data → trusted metrics → business-facing analysis**.

## Architecture

```text
TMDB API
   ↓
dlt ingestion
   ↓
PostgreSQL
   ↓
dbt transformations
   ↓
Analytics mart
   ↓
Streamlit dashboard
```

## Analytical model

The dbt layer builds:

- `analytics.stg_movies` — cleaned movie-level data
- `analytics.genre_decade_summary` — genre × decade analytical summary

Derived metrics include ROI and aggregated rating / performance measures.

## Reproduce locally

### 1. Environment

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

Copy the environment template and add your TMDB API key:

```bash
cp .env.example .env
```

Never commit `.env` or real API credentials.

### 2. Start PostgreSQL

```bash
docker compose up -d
```

### 3. Run ingestion

```bash
python pipeline.py
```

### 4. Build the analytics layer

```bash
cd analytics
dbt debug --profiles-dir .
dbt run --profiles-dir .
dbt test --profiles-dir .
```

### 5. Launch the dashboard

```bash
cd ..
streamlit run dashboard.py
```

## Key analytical questions

- Which genres deliver the strongest average ROI?
- How have ratings changed across release years?
- How does budget relate to revenue?
- Which genres and decades show different performance profiles?
- Can a reproducible data pipeline support consistent decision-making?

## Tools

**Python · pandas · PostgreSQL · SQL · dlt · dbt · Streamlit · Plotly · Docker**

## Context

Portfolio case study developed as part of an MSc Data Science project at **The American College of Greece**. The academic context is retained for transparency; the repository is structured and presented as a professional data analytics / engineering case study.

## Author

**Dimitris Bechrakis**  
Business & Data Analyst | M.Sc. Data Science
