import unittest
from datetime import date, datetime, timezone

from events import (
    event_is_relevant,
    monday_of,
    normalize_nations,
    weekend_scope_mondays,
)


class MondayOfTests(unittest.TestCase):
    def test_already_monday(self):
        self.assertEqual(monday_of(date(2026, 8, 24)), date(2026, 8, 24))

    def test_wednesday_goes_back_to_monday(self):
        self.assertEqual(monday_of(date(2026, 8, 26)), date(2026, 8, 24))

    def test_sunday_goes_back_to_monday(self):
        self.assertEqual(monday_of(date(2026, 8, 23)), date(2026, 8, 17))


class WeekendScopeMondaysTests(unittest.TestCase):
    """Fixed calendar cases for default PAST_WEEKENDS=1, FUTURE_WEEKENDS=1."""

    def test_wednesday(self):
        # 2026-08-26 Wed → past weekend week Mon 17th, upcoming weekend week Mon 24th
        self.assertEqual(
            weekend_scope_mondays(today=date(2026, 8, 26)),
            [date(2026, 8, 17), date(2026, 8, 24)],
        )

    def test_monday(self):
        self.assertEqual(
            weekend_scope_mondays(today=date(2026, 8, 24)),
            [date(2026, 8, 17), date(2026, 8, 24)],
        )

    def test_friday(self):
        self.assertEqual(
            weekend_scope_mondays(today=date(2026, 8, 21)),
            [date(2026, 8, 10), date(2026, 8, 17)],
        )

    def test_saturday_uses_this_weekend_as_upcoming(self):
        # On Saturday the "next" Saturday is today → week Mon 17th
        self.assertEqual(
            weekend_scope_mondays(today=date(2026, 8, 22)),
            [date(2026, 8, 10), date(2026, 8, 17)],
        )

    def test_sunday_skips_current_weekend_as_past(self):
        # Sunday: last fully past weekend is the previous one; next Sat is +6 days
        self.assertEqual(
            weekend_scope_mondays(today=date(2026, 8, 23)),
            [date(2026, 8, 10), date(2026, 8, 24)],
        )

    def test_future_weekends_two(self):
        self.assertEqual(
            weekend_scope_mondays(today=date(2026, 8, 26), future_weekends=2),
            [date(2026, 8, 17), date(2026, 8, 24), date(2026, 8, 31)],
        )

    def test_returns_unique_mondays_in_order(self):
        got = weekend_scope_mondays(today=date(2026, 8, 26))
        self.assertEqual(got, list(dict.fromkeys(got)))
        self.assertTrue(all(d.weekday() == 0 for d in got))


class NormalizeNationsTests(unittest.TestCase):
    def test_default_when_missing(self):
        self.assertEqual(normalize_nations(None), ["GER"])
        self.assertEqual(normalize_nations([]), ["GER"])

    def test_uppercases_and_dedupes(self):
        self.assertEqual(normalize_nations(["ger", "GER", " ned "]), ["GER", "NED"])


class EventIsRelevantTests(unittest.TestCase):
    def test_filters_by_nation_list(self):
        week = weekend_scope_mondays(today=date(2026, 8, 26))[0]
        ts = int(datetime(week.year, week.month, week.day, tzinfo=timezone.utc).timestamp())
        event = {
            "country": "GER",
            "href": "/event/2099/1/de",
            "weekStart": ts,
        }
        self.assertTrue(event_is_relevant(event, nations=["GER"]))
        self.assertFalse(event_is_relevant(event, nations=["NED"]))


if __name__ == "__main__":
    unittest.main()
