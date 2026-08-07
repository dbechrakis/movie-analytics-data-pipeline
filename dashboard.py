import os

import pandas as pd
import plotly.express as px
import streamlit as st
from dotenv import load_dotenv
from sqlalchemy import create_engine


load_dotenv()


def database_url() -> str:
    user = os.getenv("POSTGRES_USER", "itc6050")
    password = os.getenv("POSTGRES_PASSWORD", "itc6050")
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    db = os.getenv("POSTGRES_DB", "movies")
    return f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{db}"


@st.cache_data(ttl=300)
def load_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    engine = create_engine(database_url())

    movies_sql = """
        with expanded as (
            select
                m.movie_id,
                m.title,
                m.release_date,
                m.release_year,
                (floor(m.release_year / 10) * 10)::integer as decade,
                m.budget,
                m.revenue,
                m.vote_average,
                m.vote_count,
                m.popularity,
                m.roi,
                jsonb_array_elements_text(m.genre_ids::jsonb)::bigint as genre_id
            from analytics.stg_movies m
        )
        select
            expanded.*,
            g.name as genre_name
        from expanded
        left join raw.genres g
            on expanded.genre_id = g.id
    """

    mart_sql = """
        select
            genre_name,
            decade,
            total_films,
            avg_rating,
            avg_roi
        from analytics.genre_decade_summary
    """

    movies = pd.read_sql(movies_sql, engine)
    mart = pd.read_sql(mart_sql, engine)
    return movies, mart


st.set_page_config(page_title="TMDB Movie Industry Analytics", layout="wide")
st.title("TMDB Movie Industry Analytics")
st.caption("ITC 6050 final project: TMDB -> dlt -> PostgreSQL -> dbt -> Streamlit")

try:
    movie_rows, genre_decade = load_data()
except Exception as exc:
    st.error("Could not load data. Run the pipeline and dbt models first.")
    st.code("python pipeline.py\ncd analytics && dbt deps && dbt run && dbt test --profiles-dir .")
    st.exception(exc)
    st.stop()

if movie_rows.empty:
    st.warning("No movie rows available after dbt filtering.")
    st.stop()

genres = sorted(movie_rows["genre_name"].dropna().unique().tolist())
decades = sorted(movie_rows["decade"].dropna().astype(int).unique().tolist())

with st.sidebar:
    st.header("Filters")
    selected_genres = st.multiselect("Genre", genres, default=genres[: min(5, len(genres))])
    selected_decades = st.multiselect("Decade", decades, default=decades)
    min_vote_count = st.slider(
        "Minimum vote count",
        min_value=0,
        max_value=int(movie_rows["vote_count"].max()),
        value=min(100, int(movie_rows["vote_count"].max())),
        step=25,
    )

filtered = movie_rows[
    movie_rows["genre_name"].isin(selected_genres)
    & movie_rows["decade"].isin(selected_decades)
    & (movie_rows["vote_count"] >= min_vote_count)
].copy()

if filtered.empty:
    st.warning("No movies match the selected filters.")
    st.stop()

all_movie_level = movie_rows.drop_duplicates("movie_id")
movie_level = filtered.drop_duplicates("movie_id")
highest_grossing = movie_level.sort_values("revenue", ascending=False).iloc[0]

kpi1, kpi2, kpi3 = st.columns(3)
kpi1.metric("Total movies loaded", f"{all_movie_level['movie_id'].nunique():,}")
kpi2.metric("Average rating", f"{movie_level['vote_average'].mean():.2f}")
kpi3.metric("Highest grossing film", highest_grossing["title"], f"${highest_grossing['revenue']:,.0f}")

st.divider()

bar_data = (
    filtered.groupby("genre_name", as_index=False)
    .agg(avg_roi=("roi", "mean"), films=("movie_id", "nunique"))
    .sort_values("avg_roi", ascending=False)
    .head(10)
)

trend_data = (
    movie_level.groupby("release_year", as_index=False)
    .agg(avg_rating=("vote_average", "mean"), films=("movie_id", "nunique"))
    .sort_values("release_year")
)

left, right = st.columns(2)

with left:
    st.subheader("Top 10 genres by average ROI")
    st.plotly_chart(
        px.bar(
            bar_data,
            x="avg_roi",
            y="genre_name",
            orientation="h",
            color="films",
            labels={"avg_roi": "Average ROI", "genre_name": "Genre", "films": "Films"},
        ).update_layout(yaxis={"categoryorder": "total ascending"}),
        use_container_width=True,
    )

with right:
    st.subheader("Average rating by release year")
    st.plotly_chart(
        px.line(
            trend_data,
            x="release_year",
            y="avg_rating",
            markers=True,
            labels={"release_year": "Release year", "avg_rating": "Average rating"},
        ),
        use_container_width=True,
    )

st.subheader("Budget vs revenue")
st.plotly_chart(
    px.scatter(
        filtered,
        x="budget",
        y="revenue",
        color="genre_name",
        hover_name="title",
        hover_data=["release_year", "vote_average", "vote_count", "roi"],
        log_x=True,
        log_y=True,
        labels={
            "budget": "Budget (USD, log scale)",
            "revenue": "Revenue (USD, log scale)",
            "genre_name": "Genre",
        },
    ),
    use_container_width=True,
)

st.subheader("Genre and decade summary")
visible_mart = genre_decade[
    genre_decade["genre_name"].isin(selected_genres)
    & genre_decade["decade"].isin(selected_decades)
].sort_values(["decade", "genre_name"])
st.dataframe(visible_mart, use_container_width=True, hide_index=True)
