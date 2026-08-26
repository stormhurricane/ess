import yaml
import re
import json

from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, datetime, timedelta, timezone
from bs4 import BeautifulSoup

from fetch import (
    MAX_IN_FLIGHT,
    absolute_url,
    fetch,
    prefer_german_url,
    riders_url,
)

BASE_URL = "https://www.equi-score.de/"
NATION = "GER"
# Last fully past weekend + this many upcoming weekends (by calendar week)
PAST_WEEKENDS = 1
FUTURE_WEEKENDS = 1
# Concurrent HTTP: events in parallel, list pages in parallel
EVENT_WORKERS = 4
FETCH_WORKERS = 6

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
        place, date = "", "Jetzt"
        if meta:
            text = meta.get_text(" ", strip=True)
            if "·" in text:
                place, date = [p.strip() for p in text.split("·", 1)]
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
            "date": date,
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
        date = date_el.get_text(strip=True) if date_el else "Jetzt"
        locator = inner.find("div", class_="evt_locator")
        location = locator.get_text(strip=True) if locator else ""
        href = a.get("href")
        if not href:
            continue
        events.append({
            "link": prefer_german_url(href),
            "nation": nation,
            "date": date,
            "location": location,
        })
    if events:
        return events

    return parse_events_from_dom(html)

def normalize_name(name: str) -> str:
    name = name.lower().strip()
    
    if "," in name:
        parts = [p.strip() for p in name.split(",")]
        name = " ".join(parts[::-1])

    name = name.replace(".", "")
    name = re.sub(r"\s+", " ", name)

    return name


def rider_matches(found: str, search: str) -> bool:
    found_n = normalize_name(found)
    search_n = normalize_name(search)

    f_parts = found_n.split()
    s_parts = search_n.split()

    if len(f_parts) < 2 or len(s_parts) < 2:
        return False

    # Nachname muss identisch sein
    if f_parts[-1] != s_parts[-1]:
        return False

    
    f_first = f_parts[0]
    s_first = s_parts[0]

    # 1. exakt gleicher Vorname
    if f_first == s_first:
        return True

    # 2. einer ist Initiale → nur match wenn erster Buchstabe gleich
    if len(f_first) == 1 or len(s_first) == 1:
        if f_first[0] == s_first[0]:
            return True

    return False

def normalize_horse(name: str) -> str:
    name = name.lower().strip()
    # ohne Nummern
    name = re.sub(r"\s\d+$", "", name)
    return name


def _add_unique(items: list[str], value: str) -> None:
    if value and value not in items:
        items.append(value)


def parse_riders_overview(html: str) -> dict:
    """Parse /riders/ overview: 'NACHNAME, Vorname' + horses in .box_horse."""
    soup = BeautifulSoup(html, "html.parser")
    found_riders = []
    found_horses = []
    for rider_div in soup.select(".rider_name"):
        rider_name = "".join(
            t.strip() for t in rider_div.find_all(string=True, recursive=False)
        ).strip()
        _add_unique(found_riders, rider_name)

        for horse_el in rider_div.select(".box_horse b"):
            _add_unique(found_horses, horse_el.get_text(strip=True))

    return {
        "gefundene_pferde": found_horses,
        "gefundene_reiter": found_riders,
    }


def parse_competition_list(html: str) -> dict:
    """Parse startlist/resultlist pages: rider in <b>, horse in span.rider_name."""
    soup = BeautifulSoup(html, "html.parser")
    found_riders = []
    found_horses = []

    for cell in soup.select("div.td_cell"):
        bold = cell.find("b")
        if not bold:
            continue
        # Club/org line sits under the name; skip cells that are only numbers etc.
        name = bold.get_text(" ", strip=True)
        if " " not in name:
            continue
        _add_unique(found_riders, name)

    for horse_span in soup.select("span.rider_name"):
        horse_name = horse_span.get_text(" ", strip=True)
        _add_unique(found_horses, horse_name)

    return {
        "gefundene_pferde": found_horses,
        "gefundene_reiter": found_riders,
    }


def competition_list_urls(event_url: str, event_html: str) -> list[str]:
    """Collect per-class list URLs; prefer startlist over resultlist for same class."""
    soup = BeautifulSoup(event_html, "html.parser")
    by_class: dict[str, dict[str, str]] = {}

    for a in soup.select('a[href*="/startlist/"], a[href*="/resultlist/"]'):
        href = a.get("href") or ""
        kind = "startlist" if "/startlist/" in href else "resultlist"
        class_id = href.rstrip("/").split("/")[-1]
        if not class_id:
            continue
        by_class.setdefault(class_id, {})[kind] = absolute_url(event_url, href)

    urls = []
    for lists in by_class.values():
        chosen = lists.get("startlist") or lists.get("resultlist")
        if chosen:
            urls.append(chosen)
    return urls


def merge_starterlisten(*parts: dict) -> dict:
    riders = []
    horses = []
    for part in parts:
        for rider in part.get("gefundene_reiter", []):
            _add_unique(riders, rider)
        for horse in part.get("gefundene_pferde", []):
            _add_unique(horses, horse)
    return {
        "gefundene_pferde": horses,
        "gefundene_reiter": riders,
    }


def _fetch_competition_list(list_url: str) -> dict:
    try:
        return parse_competition_list(fetch(list_url))
    except Exception as exc:
        print(f"  Skip list {list_url}: {exc}")
        return {"gefundene_pferde": [], "gefundene_reiter": []}


def get_starterliste(event_url):
    event_url = prefer_german_url(event_url)
    r_url = riders_url(event_url)
    overview = parse_riders_overview(fetch(r_url))
    if overview["gefundene_reiter"]:
        return overview

    # Many events leave /riders/ empty; names live on start/result lists instead.
    event_html = fetch(event_url)
    list_urls = competition_list_urls(event_url, event_html)
    if not list_urls:
        return overview

    parts = [overview]
    with ThreadPoolExecutor(max_workers=FETCH_WORKERS) as pool:
        parts.extend(pool.map(_fetch_competition_list, list_urls))
    return merge_starterlisten(*parts)


def match_event_against_config(event, starterliste, rider_index, list_of_horses):
    """Return rider/horse hits for one event (thread-safe; no shared mutation)."""
    riders_hits = {}
    horses_hits = {}

    for gefundener_reiter in starterliste["gefundene_reiter"]:
        norm = normalize_name(gefundener_reiter)
        parts = norm.split()
        if len(parts) < 2:
            continue
        last = parts[-1]
        if last not in rider_index:
            continue
        for rider in rider_index[last]:
            if rider_matches(gefundener_reiter, rider):
                label = f"{event['location']} {event['date']} ({event['link']})"
                riders_hits.setdefault(rider.title(), []).append(label)
                break

    for horse_name in starterliste["gefundene_pferde"]:
        if not list_of_horses:
            break
        for pferd in list_of_horses:
            if normalize_horse(horse_name) == normalize_horse(pferd):
                label = (
                    event["location"]
                    + " ("
                    + event["date"]
                    + ") Link: "
                    + event["link"]
                )
                horses_hits.setdefault(horse_name, []).append(label)
                break

    return riders_hits, horses_hits


def process_event(event, rider_index, list_of_horses):
    try:
        starterliste = get_starterliste(event["link"])
    except Exception as exc:
        return event, None, exc
    hits = match_event_against_config(event, starterliste, rider_index, list_of_horses)
    return event, hits, None


if __name__ == "__main__":
    with open("config.yaml") as f:
        config = yaml.safe_load(f)
    list_of_horses = [normalize_horse(x) for x in config["horses"]]
    list_of_riders = [normalize_name(x) for x in config["riders"]]

    def build_rider_index(riders):
        index = {}
        for r in riders:
            last = r.split()[-1]
            index.setdefault(last, []).append(r)
        return index

    rider_index = build_rider_index(list_of_riders)

    events = get_events()
    no_of_events = len(events)
    scope = ", ".join(m.isoformat() for m in weekend_scope_mondays())
    print(f"Found {no_of_events} Events (weekend weeks starting {scope}).")
    print(
        f"Parallelism: {EVENT_WORKERS} event workers, "
        f"{FETCH_WORKERS} list workers, max {MAX_IN_FLIGHT} in flight."
    )
    result_dict = {
        "gefundene_pferde": {},
        "gefundene_reiter": {}
    }

    done = 0
    with ThreadPoolExecutor(max_workers=EVENT_WORKERS) as pool:
        futures = [
            pool.submit(process_event, event, rider_index, list_of_horses)
            for event in events
        ]
        for fut in as_completed(futures):
            event, hits, exc = fut.result()
            done += 1
            if exc is not None:
                print(f"Skip {event.get('location')}: {exc}")
            elif hits is not None:
                riders_hits, horses_hits = hits
                for name, labels in riders_hits.items():
                    result_dict["gefundene_reiter"].setdefault(name, []).extend(labels)
                for name, labels in horses_hits.items():
                    result_dict["gefundene_pferde"].setdefault(name, []).extend(labels)
            print(f"Progress: {'{:.1%}'.format(done / no_of_events)}")

    print("DONE")

    with open('result.json', 'w', encoding='utf-8') as f:
        json.dump(result_dict, f, ensure_ascii=False, indent=4)    
        