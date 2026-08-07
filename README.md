# ITC 6050 Final Project - Movie Industry Analytics

This repository implements the Group 2 movie analytics project:

TMDB API -> dlt -> PostgreSQL -> dbt -> Streamlit

The pipeline ingests movie metadata, genre lookup data, budgets, revenues, ratings, vote counts, and popularity from TMDB. dbt cleans the raw data, calculates ROI, and builds a genre-by-decade analytics mart for the dashboard.

## 1. Setup

Create and activate a Python virtual environment:

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

Edit `.env` and set:

```text
TMDB_API_KEY=your_real_key_here
```

Never commit `.env`.

## 2. Start PostgreSQL

```bash
docker compose up -d
```

The default database is:

- Host: `localhost`
- Port: `5432`
- Database: `movies`
- User: `itc6050`
- Password: `itc6050`

## 3. Run Ingestion

From the project root:

```bash
python pipeline.py
```

This loads two raw tables into PostgreSQL:

- `raw.movies`
- `raw.genres`

The movie ingestion uses TMDB discover results as the bounded entrypoint, then fetches movie details for each discovered ID because budget and revenue are available on the movie details endpoint.

## 4. Run dbt

```bash
cd analytics
dbt debug --profiles-dir .
dbt run --profiles-dir .
dbt test --profiles-dir .
```

dbt builds:

- `analytics.stg_movies`
- `analytics.genre_decade_summary`

## 5. Run Dashboard

From the project root:

```bash
streamlit run dashboard.py
```

The dashboard includes:

- KPI row: total movies loaded, average rating, highest grossing film.
- Bar chart: top 10 genres by average ROI.
- Line chart: average rating by release year.
- Scatter plot: budget vs revenue with genre color.
- Filters: genre, decade, minimum vote count.

## 6. Useful Checks

Confirm raw tables:

```bash
docker exec -it itc6050_movies_pg psql -U itc6050 -d movies -c "select count(*) from raw.movies;"
docker exec -it itc6050_movies_pg psql -U itc6050 -d movies -c "select count(*) from raw.genres;"
```

Confirm dbt mart:

```bash
docker exec -it itc6050_movies_pg psql -U itc6050 -d movies -c "select * from analytics.genre_decade_summary order by decade desc, total_films desc limit 10;"
```

## Author

Dimitris Bechrakis - M.Sc. Data Science, The American College of Greece
