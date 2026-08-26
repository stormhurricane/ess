import yaml
import re
import json

from concurrent.futures import ThreadPoolExecutor, as_completed

from events import get_events, weekend_scope_mondays
from fetch import MAX_IN_FLIGHT
from starters import FETCH_WORKERS, get_starterliste

# Concurrent HTTP: events in parallel
EVENT_WORKERS = 4


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
        