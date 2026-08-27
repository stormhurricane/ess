import unittest

from config_entries import active_names, entry_is_active, entry_name


class EntryNameTests(unittest.TestCase):
    def test_string(self):
        self.assertEqual(entry_name("  Ada Beispiel  "), "Ada Beispiel")

    def test_mapping(self):
        self.assertEqual(entry_name({"name": "Ada Beispiel", "active": False}), "Ada Beispiel")

    def test_empty(self):
        self.assertIsNone(entry_name(""))
        self.assertIsNone(entry_name({"name": "  "}))


class EntryIsActiveTests(unittest.TestCase):
    def test_string_always_active(self):
        self.assertTrue(entry_is_active("Ada Beispiel"))

    def test_missing_active_defaults_true(self):
        self.assertTrue(entry_is_active({"name": "Ada"}))

    def test_explicit_false(self):
        self.assertFalse(entry_is_active({"name": "Ada", "active": False}))

    def test_explicit_true(self):
        self.assertTrue(entry_is_active({"name": "Ada", "active": True}))


class ActiveNamesTests(unittest.TestCase):
    def test_filters_inactive_and_keeps_plain_strings(self):
        entries = [
            "Ada Beispiel",
            {"name": "Otto Muster", "active": False},
            {"name": "Zoe Zufall", "active": True},
        ]
        self.assertEqual(active_names(entries), ["Ada Beispiel", "Zoe Zufall"])

    def test_dedupes(self):
        self.assertEqual(
            active_names(["Ada", {"name": "Ada", "active": True}]),
            ["Ada"],
        )

    def test_empty(self):
        self.assertEqual(active_names(None), [])
        self.assertEqual(active_names([]), [])


if __name__ == "__main__":
    unittest.main()
