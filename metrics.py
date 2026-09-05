"""Metrics over the already-filtered movie–genre population."""
def genre_decade_summary(filtered):
    return (filtered.drop_duplicates(["movie_id", "genre_name"])
            .groupby(["genre_name", "decade"], as_index=False)
            .agg(total_films=("movie_id", "nunique"), avg_rating=("vote_average", "mean"), avg_roi=("roi", "mean"))
            .sort_values(["decade", "genre_name"]))
