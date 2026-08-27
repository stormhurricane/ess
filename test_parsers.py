import unittest
from pathlib import Path

from events import parse_embedded_events, parse_events_from_dom
from starters import (
    competition_list_urls,
    merge_starterlisten,
    parse_competition_list,
    parse_riders_overview,
)

FIXTURES = Path(__file__).resolve().parent / "fixtures"


def load_fixture(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


class PayloadParserTests(unittest.TestCase):
    def test_parse_embedded_events_from_next_f_push(self):
        events = parse_embedded_events(load_fixture("next_f_events.html"))
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["href"], "/event/2099/1/de")
        self.assertEqual(events[0]["country"], "GER")
        self.assertEqual(events[0]["place"], "Musterstadt")

    def test_empty_html_returns_no_events(self):
        self.assertEqual(parse_embedded_events("<html></html>"), [])


class DomEventParserTests(unittest.TestCase):
    def test_keeps_german_rows_and_prefers_de_url(self):
        events = parse_events_from_dom(load_fixture("event_rows_dom.html"))
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["location"], "Beispielhausen")
        self.assertEqual(events[0]["date"], "So 02.01.")
        self.assertTrue(events[0]["link"].endswith("/event/2099/2/de"))

    def test_skips_non_german_flag(self):
        events = parse_events_from_dom(load_fixture("event_rows_dom.html"))
        locations = [e["location"] for e in events]
        self.assertNotIn("Paris", locations)


class RidersOverviewParserTests(unittest.TestCase):
    def test_parses_comma_names_and_horses(self):
        data = parse_riders_overview(load_fixture("riders_overview.html"))
        self.assertEqual(
            data["gefundene_reiter"],
            ["BEISPIEL, Ada", "MUSTER, Otto"],
        )
        self.assertEqual(
            data["gefundene_pferde"],
            ["Sturmwolke 12", "Nebelpony"],
        )


class CompetitionListParserTests(unittest.TestCase):
    def test_parses_bold_riders_and_horse_spans(self):
        data = parse_competition_list(load_fixture("competition_list.html"))
        self.assertEqual(
            data["gefundene_reiter"],
            ["Ada Beispiel", "Otto Muster"],
        )
        self.assertEqual(
            data["gefundene_pferde"],
            ["Sturmwolke 12", "Nebelpony"],
        )

    def test_skips_single_token_bold(self):
        data = parse_competition_list(load_fixture("competition_list.html"))
        self.assertNotIn("12", data["gefundene_reiter"])


class CompetitionListUrlTests(unittest.TestCase):
    def test_prefers_startlist_over_resultlist_same_class(self):
        urls = competition_list_urls(
            "https://results.equi-score.com/event/2099/1/de",
            load_fixture("event_class_links.html"),
        )
        self.assertEqual(
            urls,
            [
                "https://results.equi-score.com/event/2099/1/startlist/18",
                "https://results.equi-score.com/event/2099/1/resultlist/14",
            ],
        )


class MergeStarterlistenTests(unittest.TestCase):
    def test_dedupes_across_parts(self):
        merged = merge_starterlisten(
            {
                "gefundene_reiter": ["Ada Beispiel"],
                "gefundene_pferde": ["Sturmwolke 12"],
            },
            {
                "gefundene_reiter": ["Ada Beispiel", "Otto Muster"],
                "gefundene_pferde": ["Nebelpony"],
            },
        )
        self.assertEqual(
            merged["gefundene_reiter"],
            ["Ada Beispiel", "Otto Muster"],
        )
        self.assertEqual(
            merged["gefundene_pferde"],
            ["Sturmwolke 12", "Nebelpony"],
        )


if __name__ == "__main__":
    unittest.main()
