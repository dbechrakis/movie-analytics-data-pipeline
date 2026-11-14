import json
from pathlib import Path
import tempfile
import unittest

from movie_analytics import snapshot_series as series


def snapshot(sampling, median, mean, ingested=100, kept=100, tests=(13, 13)):
    data = {"sampling": sampling, "movies_ingested": ingested, "movies_after_staging_filters": kept, "roi_median": median, "roi_mean": mean}
    if tests:
        data["dbt_tests"] = {"passed": tests[0], "total": tests[1]}
    return data


class SeriesTests(unittest.TestCase):
    def test_snapshots_are_read_in_profile_then_date_order_with_the_date_from_the_file_name(self):
        with tempfile.TemporaryDirectory() as folder:
            for name, data in (("2026-11-09_stratified_year.json", snapshot("stratified_year", 3.25, 6.47)),
                               ("2026-10-31_revenue.json", snapshot("revenue", 5.79, 6.85)),
                               ("2026-11-09_revenue.json", snapshot("revenue", 5.8, 6.9))):
                (Path(folder) / name).write_text(json.dumps(data))
            loaded = series.load_snapshots(Path(folder))
        self.assertEqual([(s["sampling"], s["snapshot_date"]) for s in loaded],
                         [("revenue", "2026-10-31"), ("revenue", "2026-11-09"), ("stratified_year", "2026-11-09")])

    def test_the_table_formats_each_row_and_marks_missing_test_counts(self):
        rows = series.series_table([{**snapshot("revenue", 5.7932, 6.8524, tests=None), "snapshot_date": "2026-10-31"}]).splitlines()
        self.assertEqual(rows[2], "| 2026-10-31 | `revenue` | 100 | 100 | 5.79 | 6.85 | not recorded |")

    def test_replacing_the_block_keeps_the_text_around_it(self):
        text = f"before\n{series.START}\nold\n{series.END}\nafter\n"
        self.assertEqual(series.replace_block(text, "NEW"), f"before\n{series.START}\nNEW\n{series.END}\nafter\n")

    def test_the_readme_table_matches_the_committed_snapshots(self):
        readme = series.README.read_text(encoding="utf-8")
        block = readme[readme.index(series.START) + len(series.START): readme.index(series.END)].strip("\n")
        self.assertEqual(block, series.series_table(series.load_snapshots()))


if __name__ == "__main__":
    unittest.main()
