import yaml
import json

from concurrent.futures import ThreadPoolExecutor, as_completed

from events import get_events, weekend_scope_mondays
from fetch import MAX_IN_FLIGHT
from match import (
    build_rider_index,
    match_event_against_config,
    normalize_horse,
    normalize_name,
)
from starters import FETCH_WORKERS, get_starterliste

# Concurrent HTTP: events in parallel
EVENT_WORKERS = 4


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
