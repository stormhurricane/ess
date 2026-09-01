def _event_urls(*buckets: dict) -> set[str]:
    urls: set[str] = set()
    for bucket in buckets:
        for hits in bucket.values():
            for hit in hits:
                url = hit.get("url")
                if url:
                    urls.add(url)
    return urls


def _hit_locations(hits: list) -> str:
    locations: list[str] = []
    seen: set[str] = set()
    for hit in hits:
        location = (hit.get("location") or "").strip()
        if location and location not in seen:
            seen.add(location)
            locations.append(location)
    return ", ".join(locations)


def print_result_summary(
    result_dict: dict, output_path: str, *, quiet: bool = False
) -> None:
    riders = result_dict.get("gefundene_reiter") or {}
    horses = result_dict.get("gefundene_pferde") or {}
    rider_count = len(riders)
    horse_count = len(horses)
    event_count = len(_event_urls(riders, horses))

    if rider_count == 0 and horse_count == 0:
        print("No matches found.")
    else:
        parts: list[str] = []
        if rider_count:
            label = "rider" if rider_count == 1 else "riders"
            parts.append(f"{rider_count} {label}")
        if horse_count:
            label = "horse" if horse_count == 1 else "horses"
            parts.append(f"{horse_count} {label}")
        print(f"Found {' and '.join(parts)} across {event_count} event(s).")
        if not quiet:
            for name in sorted(riders):
                print(f"  {name} → {_hit_locations(riders[name])}")
            for name in sorted(horses):
                print(f"  {name} → {_hit_locations(horses[name])}")

    print(f"Wrote {output_path}")
