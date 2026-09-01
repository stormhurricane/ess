import io
import contextlib
import unittest

from result_summary import print_result_summary


class PrintResultSummaryTests(unittest.TestCase):
    def _capture(self, result_dict, output_path="result.json", *, quiet=False):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            print_result_summary(result_dict, output_path, quiet=quiet)
        return buf.getvalue()

    def test_no_matches(self):
        out = self._capture({"gefundene_reiter": {}, "gefundene_pferde": {}})
        self.assertIn("No matches found.", out)
        self.assertIn("Wrote result.json", out)

    def test_lists_riders_horses_and_event_count(self):
        result = {
            "gefundene_reiter": {
                "BEISPIEL, Ada": [
                    {"location": "Musterstadt", "date": "Sa 01.01.", "url": "https://x/e1"},
                    {"location": "Hannover", "date": "So 02.01.", "url": "https://x/e2"},
                ],
            },
            "gefundene_pferde": {
                "Sturmwolke": [
                    {"location": "Musterstadt", "date": "Sa 01.01.", "url": "https://x/e1"},
                ],
            },
        }
        out = self._capture(result)
        self.assertIn("Found 1 rider and 1 horse across 2 event(s).", out)
        self.assertIn("BEISPIEL, Ada → Musterstadt, Hannover", out)
        self.assertIn("Sturmwolke → Musterstadt", out)

    def test_dedupes_locations_per_name(self):
        result = {
            "gefundene_reiter": {
                "Ada Beispiel": [
                    {"location": "Musterstadt", "date": "Sa 01.01.", "url": "https://x/e1"},
                    {"location": "Musterstadt", "date": "So 02.01.", "url": "https://x/e3"},
                ],
            },
            "gefundene_pferde": {},
        }
        out = self._capture(result)
        self.assertIn("Ada Beispiel → Musterstadt", out)
        self.assertNotIn("Musterstadt, Musterstadt", out)

    def test_quiet_hides_matched_names(self):
        result = {
            "gefundene_reiter": {
                "BEISPIEL, Ada": [
                    {"location": "Musterstadt", "date": "Sa 01.01.", "url": "https://x/e1"},
                ],
            },
            "gefundene_pferde": {
                "Sturmwolke": [
                    {"location": "Musterstadt", "date": "Sa 01.01.", "url": "https://x/e1"},
                ],
            },
        }
        out = self._capture(result, quiet=True)
        self.assertIn("Found 1 rider and 1 horse across 1 event(s).", out)
        self.assertIn("Wrote result.json", out)
        self.assertNotIn("BEISPIEL, Ada", out)
        self.assertNotIn("Sturmwolke", out)


if __name__ == "__main__":
    unittest.main()
