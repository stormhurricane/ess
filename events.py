import json
import re

from datetime import date, datetime, timedelta, timezone
from bs4 import BeautifulSoup

from fetch import fetch, prefer_german_url

BASE_URL = "https://www.equi-score.de/"
NATION = "GER"
# Last fully past weekend + this many upcoming weekends (by calendar week)
PAST_WEEKENDS = 1
FUTURE_WEEKENDS = 1

NEXT_F_PUSH = re.compile(
    r'self\.__next_f\.push\(\[1,"((?:\\.|[^"\\])*)"\]\)'
)


def next_f_strings(html: str) -> list[str]:
    chunks = []
    for raw in NEXT_F_PUSH.findall(html):
        try:
            chunks.append(json.loads(f'"{raw}"'))
        except json.JSONDecodeError:
            continue
    return chunks


def parse_embedded_events(html: str) -> list[dict]:
    decoder = json.JSONDecoder()
    for chunk in next_f_strings(html):
        marker = '"events":['
        idx = chunk.find(marker)
        if idx == -1:
            continue
        try:
            events, _ = decoder.raw_decode(chunk[idx + len('"events":'):])
        except json.JSONDecodeError:
            continue
        if (
            isinstance(events, list)
            and events
            and isinstance(events[0], dict)
            and "href" in events[0]
        ):
            return events
    return []


def parse_events_from_dom(html: str) -> list[dict]:
    """Fallback: nur die im HTML gerenderten Zeilen (erste zwei Wochen)."""
    soup = BeautifulSoup(html, "html.parser")
    events = []
    for a in soup.select("a.event-row"):
        href = a.get("href")
        if not href or "/event/" not in href:
            continue
        meta = a.select_one(".event-meta")
        place, date_label = "", "Jetzt"
        if meta:
            text = meta.get_text(" ", strip=True)
            if "·" in text:
                place, date_label = [p.strip() for p in text.split("·", 1)]
            else:
                place = text
        flag = a.select_one(".flag[title], .event-list-flag[title]")
        nation = NATION
        if flag and flag.get("title"):
            title = flag.get("title", "").lower()
            if title and "deutsch" not in title and "germany" not in title:
                continue
        events.append({
            "link": prefer_german_url(href),
            "nation": nation,
            "date": date_label,
            "location": place,
        })
    return events


def monday_of(day: date) -> date:
    return day - timedelta(days=day.weekday())


def weekend_scope_mondays(
    today: date | None = None,
    past_weekends: int = PAST_WEEKENDS,
    future_weekends: int = FUTURE_WEEKENDS,
) -> list[date]:
    """Mondays of: last fully past weekend week + next N upcoming weekend weeks."""
    today = today or date.today()

    if today.weekday() == 6:  # Sunday → previous week is last fully past weekend
        last_sunday = today - timedelta(days=7)
    else:
        last_sunday = today - timedelta(days=today.weekday() + 1)
    last_saturday = last_sunday - timedelta(days=1)

    mondays = [monday_of(last_saturday)]

    days_until_saturday = (5 - today.weekday()) % 7
    if today.weekday() == 5:
        next_saturday = today
    elif today.weekday() == 6:
        next_saturday = today + timedelta(days=6)
    else:
        next_saturday = today + timedelta(days=days_until_saturday)

    for i in range(future_weekends):
        mondays.append(monday_of(next_saturday + timedelta(weeks=i)))

    # preserve order, drop duplicates (e.g. edge cases around week boundaries)
    seen = set()
    unique = []
    for m in mondays:
        if m not in seen:
            seen.add(m)
            unique.append(m)
    return unique


def event_is_relevant(event: dict, nation: str = NATION) -> bool:
    if event.get("country") != nation:
        return False
    href = event.get("href") or ""
    if "/event/" not in href:
        return False
    week_start = event.get("weekStart")
    if not week_start:
        return False
    event_monday = datetime.fromtimestamp(week_start, tz=timezone.utc).date()
    return event_monday in set(weekend_scope_mondays())


def to_event_record(event: dict) -> dict:
    date_label = (event.get("date") or "").strip() or "Jetzt"
    location = (event.get("place") or event.get("title") or "").strip()
    return {
        "link": prefer_german_url(event.get("href") or ""),
        "nation": event.get("country"),
        "date": date_label,
        "location": location,
        "state": event.get("state"),
    }


def get_events():
    html = fetch(BASE_URL)

    embedded = parse_embedded_events(html)
    if embedded:
        return [to_event_record(e) for e in embedded if event_is_relevant(e)]

    # Alte Startseite (a.evt_box) oder sichtbare Zeilen der neuen Seite
    soup = BeautifulSoup(html, "html.parser")
    events = []
    for a in soup.select("a.evt_box"):
        inner = a.find("div")
        if not inner:
            continue
        nation = inner.get("data-nation")
        #FIXME bessere config nutzung
        if nation != NATION:
            continue

        date_el = inner.find("div", class_="evt_date")
        date_label = date_el.get_text(strip=True) if date_el else "Jetzt"
        locator = inner.find("div", class_="evt_locator")
        location = locator.get_text(strip=True) if locator else ""
        href = a.get("href")
        if not href:
            continue
        events.append({
            "link": prefer_german_url(href),
            "nation": nation,
            "date": date_label,
            "location": location,
        })
    if events:
        return events

    return parse_events_from_dom(html)
