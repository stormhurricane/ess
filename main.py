import json

import yaml
from concurrent.futures import ThreadPoolExecutor, as_completed

from cli import CONFIG_PATH, parse_args

from config_entries import active_search_entries
from events import get_events, weekend_scope_mondays
from fetch import MAX_IN_FLIGHT, prune_cache
from match import (
    build_rider_index,
    match_event_against_config,
    normalize_horse_base,
    normalize_name,
)
from result_summary import print_result_summary
from settings import apply_settings, load_settings
from starters import FETCH_WORKERS, get_starterliste


def process_event(event, rider_index, list_of_horses, rider_display, horse_display):
    try:
        starterliste = get_starterliste(event["link"])
    except Exception as exc:
        return event, None, exc
    hits = match_event_against_config(
        event,
        starterliste,
        rider_index,
        list_of_horses,
        rider_display=rider_display,
        horse_display=horse_display,
    )
    return event, hits, None


def load_config(path: str = CONFIG_PATH) -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


def empty_result() -> dict:
    return {"gefundene_pferde": {}, "gefundene_reiter": {}}


def merge_hits(result_dict: dict, riders_hits: dict, horses_hits: dict) -> None:
    for name, hits in riders_hits.items():
        result_dict["gefundene_reiter"].setdefault(name, []).extend(hits)
    for name, hits in horses_hits.items():
        result_dict["gefundene_pferde"].setdefault(name, []).extend(hits)


def write_result(result_dict: dict, path: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(result_dict, f, ensure_ascii=False, indent=4)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    settings = load_settings()
    if args.output:
        path = args.output.strip()
        if path:
            settings["output"] = path
    apply_settings(settings, use_cache=not args.no_cache)

    max_age = settings["cache_max_age_days"]
    if max_age > 0:
        removed = prune_cache(max_age)
        if removed:
            print(f"Cache: removed {removed} file(s) older than {max_age} days.")
    if args.no_cache:
        print("Cache: reads disabled (--no-cache).")

    config = load_config(args.config)
    nations = config.get("nations")
    list_of_horses, horse_display = active_search_entries(
        config.get("horses"), normalize_horse_base
    )
    list_of_riders, rider_display = active_search_entries(
        config.get("riders"), normalize_name
    )
    rider_index = build_rider_index(list_of_riders)

    event_workers = settings["event_workers"]
    events = get_events(nations=nations)
    no_of_events = len(events)
    scope = ", ".join(m.isoformat() for m in weekend_scope_mondays())
    print(
        f"Searching {len(list_of_riders)} riders, {len(list_of_horses)} horses."
    )
    print(f"Found {no_of_events} Events (weekend weeks starting {scope}).")
    print(
        f"Parallelism: {event_workers} event workers, "
        f"{FETCH_WORKERS} list workers, max {MAX_IN_FLIGHT} in flight."
    )

    result_dict = empty_result()
    done = 0
    with ThreadPoolExecutor(max_workers=event_workers) as pool:
        futures = [
            pool.submit(
                process_event,
                event,
                rider_index,
                list_of_horses,
                rider_display,
                horse_display,
            )
            for event in events
        ]
        for fut in as_completed(futures):
            event, hits, exc = fut.result()
            done += 1
            if exc is not None:
                print(f"Skip {event.get('location')}: {exc}")
            elif hits is not None:
                riders_hits, horses_hits = hits
                merge_hits(result_dict, riders_hits, horses_hits)
            print(f"Progress: {'{:.1%}'.format(done / no_of_events)}")

    write_result(result_dict, settings["output"])
    print_result_summary(result_dict, settings["output"])


if __name__ == "__main__":
    main()
