import yaml
import requests
import time 
import random
import re
import json
import hashlib

from bs4 import BeautifulSoup
from pathlib import Path
from urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

BASE_URL = "https://www.equi-score.de/"
HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept-Language": "de-DE,de;q=0.9",
}
NATION = "GER"
# Skips finished events older than 14 days
FINISHED_KEEP_SECONDS = 14 * 24 * 3600

CACHE_DIR = Path(".cache")
CACHE_DIR.mkdir(exist_ok=True)

NEXT_F_PUSH = re.compile(
    r'self\.__next_f\.push\(\[1,"((?:\\.|[^"\\])*)"\]\)'
)


def is_fresh(path, hours=6):
    age = time.time() - path.stat().st_mtime
    return age < hours * 3600

def cache_path(url: str) -> Path:
    h = hashlib.md5(url.encode()).hexdigest()
    return CACHE_DIR / f"{h}.html"

def fetch(url: str, use_cache=True) -> str:
    path = cache_path(url)

    if use_cache and path.exists() and is_fresh(path):
        return path.read_text(encoding="utf-8")

    time.sleep(random.uniform(1, 2))
    r = requests.get(url, headers=HEADERS, verify=False, timeout=30)
    r.raise_for_status()

    html = r.text
    path.write_text(html, encoding="utf-8")

    return html


def prefer_german_url(url: str) -> str:
    if url.endswith("/en"):
        return url[:-3] + "/de"
    return url


def riders_url(event_url: str) -> str:
    return prefer_german_url(event_url.replace("/event/", "/riders/"))


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


def event_is_relevant(event: dict, nation: str = NATION) -> bool:
    if event.get("country") != nation:
        return False
    href = event.get("href") or ""
    if "/event/" not in href:
        return False
    if event.get("state") != "finished":
        return True
    week_start = event.get("weekStart") or 0
    return week_start >= time.time() - FINISHED_KEEP_SECONDS


def to_event_record(event: dict) -> dict:
    date = (event.get("date") or "").strip() or "Jetzt"
    location = (event.get("place") or event.get("title") or "").strip()
    return {
        "link": prefer_german_url(event.get("href") or ""),
        "nation": event.get("country"),
        "date": date,
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


def get_starterliste(event_url):
    rider_url = riders_url(event_url)
    html = fetch(rider_url)
    rider_soup = BeautifulSoup(html, "html.parser")

    found_riders = []
    found_horses = []
    for rider_div in rider_soup.select(".rider_name"):
        rider_name = "".join(
            t.strip() for t in rider_div.find_all(string=True, recursive=False)
        ).strip()        
        if rider_name and not rider_name in found_riders:
            found_riders.append(rider_name)
 
        horse_names = rider_div.select(".box_horse b")
        for horse_name in horse_names:
            if horse_name:
                horse_name = horse_name.get_text(strip=True)
            if horse_name and not horse_name in found_horses:
                found_horses.append(horse_name)

    return {
        "gefundene_pferde": found_horses,
        "gefundene_reiter": found_riders
    }




if __name__ == "__main__":
    with open("config.yaml") as f:
        config = yaml.safe_load(f)
    list_of_horses = config["horses"]
    list_of_horses = [normalize_horse(x) for x in list_of_horses]
    list_of_riders = [normalize_name(x) for x in config["riders"]]

    def build_rider_index(riders):
        index = {}
        for r in list_of_riders:
            last = r.split()[-1]
            index.setdefault(last, []).append(r)
        return index

    rider_index = build_rider_index(list_of_riders)

    events = get_events()
    no_of_events = len(events)
    print(f"Found {no_of_events} Events.")
    result_dict = {
        "gefundene_pferde": {},
        "gefundene_reiter": {}
    }
    for i, event in enumerate(events):
        try:
            starterliste = get_starterliste(event["link"])
        except Exception as exc:
            print(f"Skip {event.get('location')}: {exc}")
            continue
        for gefundener_reiter in starterliste["gefundene_reiter"]:
            norm = normalize_name(gefundener_reiter)
            last = norm.split()[-1]


            if last not in rider_index:
                continue

            for rider in rider_index[last]:
                if rider_matches(gefundener_reiter, rider):
                    if rider.title() not in result_dict["gefundene_reiter"]:
                        result_dict["gefundene_reiter"][rider.title()] = []

                    event_label = f"{event['location']} {event['date']} ({event['link']})"
                    result_dict["gefundene_reiter"][rider.title()].append(event_label)
                    break
            

        for horse_name in starterliste["gefundene_pferde"]:
            if not list_of_horses:
                break
            for pferd in list_of_horses:
                if normalize_horse(horse_name) == normalize_horse(pferd):
                    if not horse_name in result_dict["gefundene_pferde"]:
                        result_dict["gefundene_pferde"][horse_name] = []
                    result_dict["gefundene_pferde"][horse_name].append(event["location"]+" ("+event["date"]+") Link: "+event["link"])
                    break

        print(f"Progress: {'{:.1%}'.format((i+1)/no_of_events)}")
    print("DONE")

    with open('result.json', 'w', encoding='utf-8') as f:
        json.dump(result_dict, f, ensure_ascii=False, indent=4)    
        