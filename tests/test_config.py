import os
import unittest
from unittest.mock import patch

from movie_analytics.config import env_int


class EnvironmentConfigTests(unittest.TestCase):
    def test_env_int_uses_default_when_missing(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(env_int("MISSING_SETTING", 5), 5)

    def test_env_int_parses_configured_value(self):
        with patch.dict(os.environ, {"PAGE_LIMIT": "12"}, clear=True):
            self.assertEqual(env_int("PAGE_LIMIT", 5), 12)

    def test_env_int_rejects_non_integer_value(self):
        with patch.dict(os.environ, {"PAGE_LIMIT": "many"}, clear=True):
            with self.assertRaises(ValueError):
                env_int("PAGE_LIMIT", 5)


if __name__ == "__main__":
    unittest.main()
