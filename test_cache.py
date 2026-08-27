import tempfile
import time
import unittest
from pathlib import Path

from fetch import prune_cache


class PruneCacheTests(unittest.TestCase):
    def test_zero_days_disables_cleanup(self):
        self.assertEqual(prune_cache(0), 0)

    def test_removes_files_older_than_max_age(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache = Path(tmp)
            old = cache / "old.html"
            fresh = cache / "fresh.html"
            old.write_text("old", encoding="utf-8")
            fresh.write_text("fresh", encoding="utf-8")
            now = time.time()
            import os

            os.utime(old, (now - 20 * 86400, now - 20 * 86400))
            os.utime(fresh, (now, now))

            # Patch CACHE_DIR for test
            import fetch
            original = fetch.CACHE_DIR
            fetch.CACHE_DIR = cache
            try:
                removed = prune_cache(14)
                self.assertEqual(removed, 1)
                self.assertFalse(old.exists())
                self.assertTrue(fresh.exists())
            finally:
                fetch.CACHE_DIR = original

    def test_missing_cache_dir(self):
        import fetch
        original = fetch.CACHE_DIR
        fetch.CACHE_DIR = Path("/tmp/ess-cache-prune-missing-dir")
        try:
            self.assertEqual(prune_cache(7), 0)
        finally:
            fetch.CACHE_DIR = original


if __name__ == "__main__":
    unittest.main()
