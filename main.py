import yaml

import requests
import time 
import random

from bs4 import BeautifulSoup
import re

import json

COUNTRY_MAP = {
    "Deutschland": {
        "kurzel": "GER"
    }
}

BASE = "https://www.equi-score.de/"

import hashlib
import os
from pathlib import Path

CACHE_DIR = Path(".cache")
CACHE_DIR.mkdir(exist_ok=True)

def is_fresh(path, hours=6):
    age = time.time() - path.stat().st_mtime
    return age < hours * 3600

def cache_path(url: str) -> Path:
    h = hashlib.md5(url.encode()).hexdigest()
    return CACHE_DIR / f"{h}.html"

def fetch(url: str, use_cache=True) -> str:
    path = cache_path(url)

    if use_cache and path.exists() and is_fresh(path):
        return path.read_text()

    time.sleep(random.uniform(1, 2))
    r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
    r.raise_for_status()

    html = r.text
    path.write_text(html)

    return html

def get_events(config = None):
    html = fetch(BASE)

    soup = BeautifulSoup(html, "html.parser")
    
    events = []

    for a in soup.select("a.evt_box"):
        inner = a.find("div")
        if not inner:
            continue
        nation = inner.get("data-nation")
        #FIXME bessere config nutzung
        if nation != "GER":
            continue
            
        date = inner.find("div", class_="evt_date")
        if date:
            date = date.text
        else:
            date = "Jetzt"
        location = inner.find("div", class_="evt_locator").text

        
        href = a.get("href")
        event = {
            "link": href,
            "nation": nation,
            "date": date,
            "location": location

        }
        events.append(event)
    
    return events

def normalize_name(name: str) -> str:
    name = name.lower().strip()

    # "mustermann, max" → "max mustermann"
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
    name = re.sub(r"\s\d+$", "", name)
    return name

def get_starterliste(event_url):
    rider_url = event_url.replace("/event/", "/riders/")
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
        "pferde": found_horses,
        "reiter": found_riders
    }




if __name__ == "__main__":
    with open("config.yaml") as f:
        config = yaml.safe_load(f)
    horses = config["horses"]
    horses = [normalize_horse(x) for x in horses]
    riders = [normalize_name(x) for x in config["riders"]]

    def build_rider_index(riders):
        index = {}
        for r in riders:
            last = r.split()[-1]
            index.setdefault(last, []).append(r)
        return index

    rider_index = build_rider_index(riders)

    events = get_events()
    no_of_events = len(events)
    print(f"Found {no_of_events} Events.")
    result_dict = {
        "pferde": {},
        "reiter": {}
    }
    for i, event in enumerate(events):
        starterliste = get_starterliste(event["link"])
        for reiter in starterliste["reiter"]:
            norm = normalize_name(reiter)
            last = norm.split()[-1]


            if last not in rider_index:
                continue

            for rider in rider_index[last]:
                if rider_matches(reiter, rider):
                    if rider.title() not in result_dict["reiter"]:
                        result_dict["reiter"][rider.title()] = []

                    event_label = f"{event['location']} {event['date']} ({event['link']})"
                    result_dict["reiter"][rider.title()].append(event_label)
                    break
            

        for horse_name in starterliste["pferde"]:
            if not horses:
                break
            for pferd in horses:
                if normalize_horse(horse_name) == normalize_horse(pferd):
                    if not horse_name in result_dict["pferde"]:
                        result_dict["pferde"][horse_name] = []
                    result_dict["pferde"][horse_name].append(event["location"]+" ("+event["date"]+") Link: "+event["link"])
                    break

        print(f"Progress: {'{:.1%}'.format((i+1)/no_of_events)}")
    print("DONE")

    with open('result.json', 'w', encoding='utf-8') as f:
        json.dump(result_dict, f, ensure_ascii=False, indent=4)    
    # class box_title, "Woche" In div (Diese oder nächste)
    # vielleicht matchingm iwe viele (ist in klammern)