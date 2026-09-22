import unittest

import pandas as pd

from movie_analytics.metrics import SUMMARY_COLUMNS, genre_decade_summary


class SummaryTests(unittest.TestCase):
    def test_summary_uses_filtered_population(self):
        frame = pd.DataFrame(
            [
                dict(movie_id=1, genre_name="Drama", decade=2020, vote_count=500, vote_average=8.0, roi=2.0),
                dict(movie_id=2, genre_name="Drama", decade=2020, vote_count=10, vote_average=2.0, roi=20.0),
                dict(movie_id=1, genre_name="Comedy", decade=2020, vote_count=500, vote_average=8.0, roi=2.0),
            ]
        )
        result = genre_decade_summary(frame[frame.vote_count >= 100]).set_index("genre_name")
        self.assertEqual(result.loc["Drama", "total_films"], 1)
        self.assertEqual(result.loc["Drama", "avg_rating"], 8.0)
        self.assertEqual(result.loc["Drama", "avg_roi"], 2.0)
        self.assertEqual(result.loc["Comedy", "total_films"], 1)

    def test_summary_deduplicates_movie_genre_pairs(self):
        duplicated = pd.DataFrame(
            [
                dict(movie_id=1, genre_name="Drama", decade=2020, vote_average=8.0, roi=2.0),
                dict(movie_id=1, genre_name="Drama", decade=2020, vote_average=8.0, roi=2.0),
            ]
        )
        result = genre_decade_summary(duplicated).iloc[0]
        self.assertEqual(result["total_films"], 1)
        self.assertEqual(result["avg_rating"], 8.0)

    def test_empty_summary_has_stable_schema(self):
        result = genre_decade_summary(pd.DataFrame())
        self.assertTrue(result.empty)
        self.assertEqual(result.columns.tolist(), SUMMARY_COLUMNS)

if __name__ == "__main__":
    unittest.main()
