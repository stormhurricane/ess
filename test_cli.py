import unittest

from cli import CONFIG_PATH, parse_args
from settings import SETTINGS_PATH


class ParseArgsTests(unittest.TestCase):
    def test_defaults(self):
        args = parse_args([])
        self.assertEqual(args.config, CONFIG_PATH)
        self.assertEqual(args.settings, SETTINGS_PATH)
        self.assertIsNone(args.output)
        self.assertFalse(args.no_cache)

    def test_config_and_output(self):
        args = parse_args(["--config", "other.yaml", "--output", "out.json"])
        self.assertEqual(args.config, "other.yaml")
        self.assertEqual(args.settings, SETTINGS_PATH)
        self.assertEqual(args.output, "out.json")

    def test_settings(self):
        args = parse_args(["--settings", "data/settings.json"])
        self.assertEqual(args.settings, "data/settings.json")

    def test_no_cache(self):
        args = parse_args(["--no-cache"])
        self.assertTrue(args.no_cache)


if __name__ == "__main__":
    unittest.main()
