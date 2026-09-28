"""The response checks run without a TMDB key, database, or dlt installation."""

import unittest

from movie_analytics.contracts import discovery_results, movie_details


class SourceContractTests(unittest.TestCase):
    def test_discovery_allows_later_empty_page(self):
        self.assertEqual(discovery_results({"results": []}, 2), [])

    def test_discovery_rejects_malformed_or_empty_first_page(self):
        for payload in ({}, {"results": None}, {"results": []}, {"results": [None]}):
            with self.subTest(payload=payload), self.assertRaises(ValueError):
                discovery_results(payload, 1)

    def test_details_require_matching_id_title_and_genres(self):
        good = {"id": 7, "title": "Example", "genres": []}
        self.assertEqual(movie_details(good, 7), good)
        for bad in ({"id": 8, "title": "Example", "genres": []},
                    {"id": 7, "genres": []}, {"id": 7, "title": "Example"}):
            with self.subTest(payload=bad), self.assertRaises(ValueError):
                movie_details(bad, 7)


if __name__ == "__main__":
    unittest.main()
