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

def fetch(url: str) -> str:
    time.sleep(random.uniform(1, 2))
    r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
    r.raise_for_status()
    return r.text

def get_events(config = None):
    html = fetch(BASE)
    soup = BeautifulSoup(html, "html.parser")
    
    events = []

    count = 0

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


def get_starterliste(event_url):
    rider_url = event_url.replace("event", "riders")
    html = fetch(rider_url)
    rider_soup = BeautifulSoup(html, "html.parser")

    found_riders = []
    found_horses = []
    for rider_div in rider_soup.select(".rider_name"):
        rider_name = "".join(
            t.strip() for t in rider_div.find_all(string=True, recursive=False)
        ).strip()        
        if not rider_name in found_riders:
            found_riders.append(rider_name)
 
        horse_name = rider_div.select_one(".box_horse b")
        if horse_name:
            horse_name = horse_name.get_text(strip=True)
        if horse_name and not horse_name in found_horses:
            found_horses.append(horse_name)

       # print(found_riders)
    return {
        "pferde": found_horses,
        "reiter": found_riders
    }




if __name__ == "__main__":
    with open("config.yaml") as f:
        config = yaml.safe_load(f)
    horses = config["horses"]
    riders = config["riders"]

    events = get_events()
    no_of_events = len(events)
    # with open("event_cache_testing.json") as f:
    #     events = json.load(f)
    # events = json.load("event_cache_testing.json")
    result_dict = {}
    for i, event in enumerate(events):
        starterliste = get_starterliste(event["link"])
        for reiter in starterliste["reiter"]:
            if not riders:
                break
            namen = reiter.split(",")
            namen = [x.strip().title() for x in reiter.split(",")]
            namen.reverse()
            reiter_name = " ".join(namen)
            if reiter_name in riders:
                if not reiter_name in result_dict:
                    result_dict[reiter_name] = []
                result_dict[reiter_name].append(event["location"]+" "+event["date"])
            

        for horse in starterliste["pferde"]:
            pass

        print(f"Progress: {'{:.1%}'.format(i/no_of_events)}")
    print("DONE")

    with open('result.json', 'w', encoding='utf-8') as f:
        json.dump(result_dict, f, ensure_ascii=False, indent=4)    
    # class box_title, "Woche" In div (Diese oder nächste)
    # vielleicht matchingm iwe viele (ist in klammern)