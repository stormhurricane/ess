import re


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


def normalize_horse_base(name: str) -> str:
    name = name.lower().strip()
    return re.sub(r"\s+", " ", name)


_TRAILING_START_NUMBER = re.compile(r"\s\d+$")


def horse_config_has_start_number(name: str) -> bool:
    return bool(_TRAILING_START_NUMBER.search(normalize_horse_base(name)))


def normalize_horse(name: str, *, strip_trailing_number: bool = False) -> str:
    name = normalize_horse_base(name)
    if strip_trailing_number:
        name = _TRAILING_START_NUMBER.sub("", name)
    return name


def horse_matches(found: str, search: str) -> bool:
    """Match found list name against config horse.

    Config without trailing start number (e.g. Chili): ignore number on found side.
    Config with trailing number (e.g. Diamond 110): exact match including number.
    """
    search_n = normalize_horse_base(search)
    if horse_config_has_start_number(search):
        return normalize_horse_base(found) == search_n
    return normalize_horse(found, strip_trailing_number=True) == search_n


def build_rider_index(riders: list[str]) -> dict[str, list[str]]:
    index: dict[str, list[str]] = {}
    for r in riders:
        last = r.split()[-1]
        index.setdefault(last, []).append(r)
    return index


def format_event_label(event) -> str:
    """Single display label for a hit: location, date, link."""
    location = (event.get("location") or "").strip()
    date = (event.get("date") or "").strip()
    link = (event.get("link") or "").strip()
    return f"{location} {date} ({link})"


def match_event_against_config(
    event,
    starterliste,
    rider_index,
    list_of_horses,
    *,
    rider_display: dict[str, str] | None = None,
    horse_display: dict[str, str] | None = None,
):
    """Return rider/horse hits for one event (thread-safe; no shared mutation)."""
    rider_display = rider_display or {}
    horse_display = horse_display or {}
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
                label = format_event_label(event)
                riders_hits.setdefault(rider_display.get(rider, rider), []).append(label)
                break

    for horse_name in starterliste["gefundene_pferde"]:
        if not list_of_horses:
            break
        for pferd in list_of_horses:
            if horse_matches(horse_name, pferd):
                label = format_event_label(event)
                horses_hits.setdefault(horse_display.get(pferd, pferd), []).append(label)
                break

    return riders_hits, horses_hits
