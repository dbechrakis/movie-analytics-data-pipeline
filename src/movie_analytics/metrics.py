"""Business metrics over the filtered movie–genre population."""

import pandas as pd


SUMMARY_COLUMNS = ["genre_name", "decade", "total_films", "avg_rating", "avg_roi"]


def genre_decade_summary(filtered: pd.DataFrame) -> pd.DataFrame:
    """Aggregate unique movie–genre pairs by genre and release decade."""
    if filtered.empty:
        return pd.DataFrame(columns=SUMMARY_COLUMNS)

    return (
        filtered.drop_duplicates(["movie_id", "genre_name"])
        .groupby(["genre_name", "decade"], as_index=False)
        .agg(
            total_films=("movie_id", "nunique"),
            avg_rating=("vote_average", "mean"),
            avg_roi=("roi", "mean"),
        )
        .sort_values(["decade", "genre_name"])
        .reset_index(drop=True)
    )
