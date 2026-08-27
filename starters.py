from concurrent.futures import ThreadPoolExecutor

from bs4 import BeautifulSoup

from fetch import absolute_url, fetch, prefer_german_url, riders_url

# Concurrent fetches for per-class start/result lists
FETCH_WORKERS = 6


def apply_settings(*, fetch_workers: int | None = None) -> None:
    global FETCH_WORKERS
    if fetch_workers is not None:
        FETCH_WORKERS = fetch_workers


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
