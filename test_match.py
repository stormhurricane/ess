import unittest

from match import (
    build_rider_index,
    horse_matches,
    match_event_against_config,
    normalize_horse,
    normalize_horse_base,
    normalize_name,
    rider_matches,
)


class NormalizeNameTests(unittest.TestCase):
    def test_lower_and_strip(self):
        self.assertEqual(normalize_name("  Ada Beispiel  "), "ada beispiel")

    def test_comma_last_first(self):
        self.assertEqual(normalize_name("BEISPIEL, Ada"), "ada beispiel")

    def test_drops_dots_and_collapses_spaces(self):
        self.assertEqual(normalize_name("A.  Beispiel"), "a beispiel")


class NormalizeHorseTests(unittest.TestCase):
    def test_lower_and_strip(self):
        self.assertEqual(normalize_horse_base("  Sturmwolke  "), "sturmwolke")

    def test_strips_trailing_start_number_only_when_asked(self):
        self.assertEqual(
            normalize_horse("Sturmwolke 12", strip_trailing_number=True),
            "sturmwolke",
        )
        self.assertEqual(
            normalize_horse("Sturmwolke 12", strip_trailing_number=False),
            "sturmwolke 12",
        )

    def test_keeps_numbers_inside_name(self):
        self.assertEqual(
            normalize_horse_base("Star 110 Flash"),
            "star 110 flash",
        )


class HorseMatchesTests(unittest.TestCase):
    def test_config_without_number_matches_found_with_start_number(self):
        self.assertTrue(horse_matches("Sturmwolke 12", "Sturmwolke"))

    def test_config_with_number_requires_exact_match(self):
        self.assertTrue(horse_matches("Star 110 Flash", "Star 110 Flash"))
        self.assertFalse(horse_matches("Star 110 Flash", "Star 110"))
        self.assertFalse(horse_matches("Star 99 Flash", "Star 110 Flash"))

    def test_config_with_number_rejects_different_start_number(self):
        self.assertTrue(horse_matches("Diamond 110", "Diamond 110"))
        self.assertFalse(horse_matches("Diamond 99", "Diamond 110"))
        self.assertFalse(horse_matches("Diamond", "Diamond 110"))


class RiderMatchesTests(unittest.TestCase):
    def test_exact_first_and_last(self):
        self.assertTrue(rider_matches("BEISPIEL, Ada", "Ada Beispiel"))

    def test_initial_matches_same_first_letter(self):
        self.assertTrue(rider_matches("A. Beispiel", "Ada Beispiel"))
        self.assertTrue(rider_matches("Ada Beispiel", "A. Beispiel"))

    def test_different_first_name_rejected(self):
        self.assertFalse(rider_matches("Otto Beispiel", "Ada Beispiel"))

    def test_different_last_name_rejected(self):
        self.assertFalse(rider_matches("Ada Anders", "Ada Beispiel"))

    def test_single_token_rejected(self):
        self.assertFalse(rider_matches("Beispiel", "Ada Beispiel"))
        self.assertFalse(rider_matches("Ada Beispiel", "Beispiel"))

    def test_wrong_initial_rejected(self):
        self.assertFalse(rider_matches("O. Beispiel", "Ada Beispiel"))


class BuildRiderIndexTests(unittest.TestCase):
    def test_groups_by_last_name(self):
        index = build_rider_index(
            ["ada beispiel", "otto muster", "zoe zufall"]
        )
        self.assertEqual(index["beispiel"], ["ada beispiel"])
        self.assertEqual(index["muster"], ["otto muster"])
        self.assertEqual(index["zufall"], ["zoe zufall"])


class MatchEventAgainstConfigTests(unittest.TestCase):
    def setUp(self):
        self.event = {
            "location": "Musterstadt",
            "date": "Sa 01.01.",
            "link": "https://results.equi-score.com/event/2099/1/de",
        }
        self.rider_index = build_rider_index(["ada beispiel", "otto muster"])
        self.horses = ["sturmwolke", "star 110 flash"]

    def test_matches_rider_and_horse(self):
        starterliste = {
            "gefundene_reiter": ["BEISPIEL, Ada"],
            "gefundene_pferde": ["Sturmwolke 12"],
        }
        riders, horses = match_event_against_config(
            self.event, starterliste, self.rider_index, self.horses
        )
        self.assertIn("Ada Beispiel", riders)
        self.assertEqual(
            riders["Ada Beispiel"],
            [
                "Musterstadt Sa 01.01. "
                "(https://results.equi-score.com/event/2099/1/de)"
            ],
        )
        self.assertIn("Sturmwolke 12", horses)
        self.assertEqual(
            horses["Sturmwolke 12"],
            [
                "Musterstadt (Sa 01.01.) Link: "
                "https://results.equi-score.com/event/2099/1/de"
            ],
        )

    def test_numbered_config_horse_matches_exactly(self):
        starterliste = {
            "gefundene_reiter": [],
            "gefundene_pferde": ["Star 110 Flash", "Star 99 Flash"],
        }
        _, horses = match_event_against_config(
            self.event, starterliste, self.rider_index, self.horses
        )
        self.assertIn("Star 110 Flash", horses)
        self.assertNotIn("Star 99 Flash", horses)

    def test_ignores_unrelated_names(self):
        starterliste = {
            "gefundene_reiter": ["Zufall, Zoe"],
            "gefundene_pferde": ["Mondlicht 3"],
        }
        riders, horses = match_event_against_config(
            self.event, starterliste, self.rider_index, self.horses
        )
        self.assertEqual(riders, {})
        self.assertEqual(horses, {})


if __name__ == "__main__":
    unittest.main()
