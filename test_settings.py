import tempfile
import unittest
from pathlib import Path

from settings import DEFAULTS, MAX, MIN, load_settings, normalize_settings


class NormalizeSettingsTests(unittest.TestCase):
    def test_defaults_when_empty(self):
        got = normalize_settings(None)
        self.assertEqual(got["event_workers"], DEFAULTS["event_workers"])
        self.assertEqual(got["output"], "result.json")

    def test_clamps_workers_to_max(self):
        got = normalize_settings({"event_workers": 999, "fetch_workers": 999})
        self.assertEqual(got["event_workers"], MAX["event_workers"])
        self.assertEqual(got["fetch_workers"], MAX["fetch_workers"])

    def test_clamps_workers_to_min(self):
        got = normalize_settings({"event_workers": 0, "max_in_flight": -3})
        self.assertEqual(got["event_workers"], MIN["event_workers"])
        self.assertEqual(got["max_in_flight"], MIN["max_in_flight"])

    def test_swaps_inverted_delay_range(self):
        got = normalize_settings(
            {"request_delay_min": 1.0, "request_delay_max": 0.1}
        )
        self.assertLessEqual(got["request_delay_min"], got["request_delay_max"])

    def test_invalid_numbers_fall_back_via_clamp(self):
        got = normalize_settings({"cache_hours": "nope"})
        self.assertEqual(got["cache_hours"], DEFAULTS["cache_hours"])

    def test_output_path(self):
        got = normalize_settings({"output": "  out/hits.json  "})
        self.assertEqual(got["output"], "out/hits.json")

    def test_cache_max_age_days_default_and_clamp(self):
        got = normalize_settings(None)
        self.assertEqual(got["cache_max_age_days"], DEFAULTS["cache_max_age_days"])
        self.assertEqual(normalize_settings({"cache_max_age_days": 0})["cache_max_age_days"], 0)
        self.assertEqual(
            normalize_settings({"cache_max_age_days": 999})["cache_max_age_days"],
            MAX["cache_max_age_days"],
        )


class LoadSettingsTests(unittest.TestCase):
    def test_missing_file_uses_defaults(self):
        got = load_settings("/tmp/ess-settings-does-not-exist.json")
        self.assertEqual(got["max_in_flight"], DEFAULTS["max_in_flight"])

    def test_loads_and_clamps_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "settings.json"
            path.write_text(
                '{"event_workers": 100, "output": "x.json"}',
                encoding="utf-8",
            )
            got = load_settings(path)
            self.assertEqual(got["event_workers"], MAX["event_workers"])
            self.assertEqual(got["output"], "x.json")


if __name__ == "__main__":
    unittest.main()
