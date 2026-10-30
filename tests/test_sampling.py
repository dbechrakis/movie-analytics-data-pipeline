import os
import unittest
from unittest.mock import patch

from movie_analytics.sampling import PROFILES, Sampling


class RevenueProfileTests(unittest.TestCase):
    def test_default_requests_match_the_original_ingestion(self):
        requests = list(Sampling().requests())
        self.assertEqual([r["page"] for r in requests], [1, 2, 3, 4, 5])
        for request in requests:
            self.assertEqual(request["sort_by"], "revenue.desc")
            self.assertEqual(request["vote_count.gte"], 50)
            self.assertEqual((request["include_adult"], request["include_video"]), ("false", "false"))
            self.assertNotIn("primary_release_year", request)

    def test_configured_sort_and_page_count_are_used(self):
        requests = list(Sampling(max_pages=2, sort_by="popularity.desc").requests())
        self.assertEqual([(r["page"], r["sort_by"]) for r in requests],
                         [(1, "popularity.desc"), (2, "popularity.desc")])


class StratifiedProfileTests(unittest.TestCase):
    def test_every_year_is_requested_and_ranking_ignores_revenue(self):
        sampling = Sampling(profile="stratified_year", year_from=2018, year_to=2020, pages_per_year=2)
        requests = list(sampling.requests())
        self.assertEqual([(r["primary_release_year"], r["page"]) for r in requests],
                         [(2018, 1), (2018, 2), (2019, 1), (2019, 2), (2020, 1), (2020, 2)])
        self.assertEqual({r["sort_by"] for r in requests}, {"vote_count.desc"})

    def test_the_revenue_sort_setting_does_not_leak_into_the_stratified_profile(self):
        sampling = Sampling(profile="stratified_year", sort_by="revenue.desc", year_from=2020, year_to=2020)
        self.assertEqual(next(sampling.requests())["sort_by"], "vote_count.desc")

    def test_a_single_year_is_allowed(self):
        self.assertEqual(len(list(Sampling(profile="stratified_year", year_from=2020, year_to=2020).requests())), 1)


class ValidationTests(unittest.TestCase):
    def test_unknown_profile_and_bad_ranges_are_rejected(self):
        for kwargs in ({"profile": "random"}, {"max_pages": 0}, {"pages_per_year": 0},
                       {"year_from": 2021, "year_to": 2020}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                Sampling(**kwargs)

    def test_profiles_are_the_documented_ones(self):
        self.assertEqual(PROFILES, ("revenue", "stratified_year"))


class EnvironmentTests(unittest.TestCase):
    def test_empty_environment_gives_the_defaults(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(Sampling.from_env(), Sampling())

    def test_blank_values_fall_back_to_the_defaults(self):
        with patch.dict(os.environ, {"TMDB_SAMPLING": "", "TMDB_DISCOVER_SORT_BY": ""}, clear=True):
            self.assertEqual(Sampling.from_env(), Sampling())

    def test_configured_values_are_parsed(self):
        env = {"TMDB_SAMPLING": "stratified_year", "TMDB_YEAR_FROM": "2010", "TMDB_YEAR_TO": "2012",
               "TMDB_PAGES_PER_YEAR": "3", "TMDB_VOTE_COUNT_GTE": "200"}
        with patch.dict(os.environ, env, clear=True):
            sampling = Sampling.from_env()
        self.assertEqual((sampling.profile, sampling.year_from, sampling.year_to, sampling.pages_per_year,
                          sampling.vote_count_gte), ("stratified_year", 2010, 2012, 3, 200))


if __name__ == "__main__":
    unittest.main()
