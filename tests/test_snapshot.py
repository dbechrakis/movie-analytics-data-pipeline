import json
from pathlib import Path
import tempfile
import unittest

from movie_analytics.snapshot import dbt_test_counts, rounded


class SnapshotHelperTests(unittest.TestCase):
    def test_dbt_counts_passes_and_total(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "run_results.json"
            path.write_text(json.dumps({"results": [{"status": "pass"}, {"status": "pass"}, {"status": "fail"}]}))
            self.assertEqual(dbt_test_counts(path), {"passed": 2, "total": 3})

    def test_missing_dbt_results_are_reported_as_none_not_zero(self):
        self.assertIsNone(dbt_test_counts(Path("/nonexistent/run_results.json")))

    def test_rounding_keeps_none(self):
        self.assertIsNone(rounded(None))
        self.assertEqual(rounded(1.23456, 2), 1.23)


if __name__ == "__main__":
    unittest.main()
