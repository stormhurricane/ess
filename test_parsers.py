import unittest
from pathlib import Path

from events import (
    parse_embedded_events,
    parse_events_from_dom,
    parse_events_from_evt_box,
)
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

    def test_respects_nations_filter(self):
        events = parse_events_from_dom(
            load_fixture("event_rows_dom.html"),
            nations=["NED"],
        )
        self.assertEqual(events, [])


class DomEventParserRobustnessTests(unittest.TestCase):
    def test_empty_html(self):
        self.assertEqual(parse_events_from_dom(""), [])
        self.assertEqual(parse_events_from_dom(None), [])

    def test_sparse_rows_without_crash(self):
        events = parse_events_from_dom(load_fixture("event_rows_sparse.html"))
        self.assertEqual(len(events), 2)
        by_link = {e["link"].split("/")[-2]: e for e in events}
        self.assertEqual(by_link["5"]["location"], "Nur Ort")
        self.assertEqual(by_link["5"]["date"], "Jetzt")
        self.assertEqual(by_link["6"]["location"], "")
        self.assertEqual(by_link["6"]["date"], "Jetzt")


class EvtBoxParserTests(unittest.TestCase):
    def test_parses_minimal_evt_box(self):
        events = parse_events_from_evt_box(load_fixture("evt_box_sparse.html"))
        self.assertEqual(len(events), 1)
        self.assertTrue(events[0]["link"].endswith("/event/2099/7/de"))
        self.assertEqual(events[0]["date"], "Jetzt")
        self.assertEqual(events[0]["location"], "")

    def test_empty_html(self):
        self.assertEqual(parse_events_from_evt_box(""), [])


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

    def test_skips_empty_rider_blocks(self):
        data = parse_riders_overview(load_fixture("riders_sparse.html"))
        self.assertEqual(data["gefundene_reiter"], ["BEISPIEL, Ada"])
        self.assertEqual(data["gefundene_pferde"], [])

    def test_empty_html(self):
        self.assertEqual(
            parse_riders_overview(""),
            {"gefundene_pferde": [], "gefundene_reiter": []},
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

    def test_sparse_html_without_crash(self):
        data = parse_competition_list(load_fixture("competition_list_sparse.html"))
        self.assertEqual(data["gefundene_reiter"], ["Ada Beispiel"])
        self.assertEqual(data["gefundene_pferde"], ["Sturmwolke 12"])

    def test_empty_html(self):
        self.assertEqual(
            parse_competition_list(""),
            {"gefundene_pferde": [], "gefundene_reiter": []},
        )


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

    def test_skips_malformed_class_links(self):
        urls = competition_list_urls(
            "https://results.equi-score.com/event/2099/1/de",
            load_fixture("event_class_links_broken.html"),
        )
        self.assertEqual(
            urls,
            ["https://results.equi-score.com/event/2099/1/startlist/99"],
        )

    def test_empty_html(self):
        self.assertEqual(competition_list_urls("https://x/event/1/de", ""), [])


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

    def test_ignores_none_parts(self):
        merged = merge_starterlisten(
            None,
            {"gefundene_reiter": ["Ada Beispiel"], "gefundene_pferde": []},
        )
        self.assertEqual(merged["gefundene_reiter"], ["Ada Beispiel"])


if __name__ == "__main__":
    unittest.main()
