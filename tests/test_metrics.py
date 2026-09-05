import unittest
import pandas as pd
from metrics import genre_decade_summary

class SummaryTests(unittest.TestCase):
    def test_summary_uses_filtered_population(self):
        frame=pd.DataFrame([
            dict(movie_id=1,genre_name='Drama',decade=2020,vote_count=500,vote_average=8.,roi=2.),
            dict(movie_id=2,genre_name='Drama',decade=2020,vote_count=10,vote_average=2.,roi=20.),
            dict(movie_id=1,genre_name='Comedy',decade=2020,vote_count=500,vote_average=8.,roi=2.)])
        result=genre_decade_summary(frame[frame.vote_count>=100]).set_index('genre_name')
        self.assertEqual(result.loc['Drama','total_films'],1)
        self.assertEqual(result.loc['Drama','avg_rating'],8.)
        self.assertEqual(result.loc['Drama','avg_roi'],2.)
        self.assertEqual(result.loc['Comedy','total_films'],1)

if __name__=='__main__':unittest.main()
