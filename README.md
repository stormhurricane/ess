# ESS — Equi-Score Scraper

Sucht auf [equi-score.de](https://www.equi-score.de/) deutsche Turniere und prüft,
ob konfigurierte Reiter oder Pferde in den Starterlisten stehen.

Ergebnis: `result.json`.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp config.example.yaml config.yaml
```

In `config.yaml` die zu suchenden Reiter und Pferde eintragen. Diese Datei ist
gitignored und gehört nicht ins Repo.

## Nutzung

```bash
python main.py
```

Das Skript:

1. lädt die Event-Übersicht aus dem Next.js-Payload (alle Wochen, nicht nur die ersten zwei im UI)
2. filtert nach Nation (`GER`) und Zeitfenster: **letztes Wochenende** (Vergangenheit) plus das **nächste Wochenende** (jeweils die ganze Kalenderwoche)
3. holt je Event die Starterliste (`/riders/`); ist die leer, die Klassen-`startlist`/`resultlist`-Seiten
4. gleicht Namen mit der Config ab
5. schreibt Treffer nach `result.json`

Die öffentliche Startseite paginiert (`Load more`) und zeigt standardmäßig nur die aktuelle plus die letzte Kalenderwoche. Die Eventliste selbst steckt vollständig in der Seite — der Scraper liest diese Payload statt sichtbarer HTML-Karten.

Viele Turniere lassen `/riders/` leer; Reiter und Pferde stehen dann nur in den Prüfungs-Start-/Ergebnislisten. Der Scraper fällt in dem Fall darauf zurück (bevorzugt `startlist`).

HTTP-Antworten werden unter `.cache/` für 6 Stunden zwischengespeichert.
Leere `/riders/`-Seiten nur **15 Minuten** (Listen werden oft später nachgeliefert).
Requests laufen parallel (Events + Startlisten), begrenzt auf max. 8 gleichzeitige
Verbindungen, mit kurzer Pause (0,2–0,5 s) pro Netz-Request. Pro Worker-Thread
wird eine `requests.Session` mit Keep-Alive wiederverwendet.

## Konfiguration

Vorlage: `config.example.yaml`

```yaml
riders:
  - Max Mustermann

horses:
  - Epona

nations:
  - GER
```

- **Reiter:** Nachname muss passen; Vorname exakt oder als Initiale (`L. Mustermann`).
- **Pferde:** Vergleich ohne Groß/Kleinschreibung; eine Nummer am Ende (`Chili 57`)
  wird aktuell abgeschnitten — kurze Namen können zu Falschtreffern führen.

## Ausgabe

`result.json` gruppiert Treffer nach Reiter und Pferd, jeweils mit Ort, Datum und Link.

`.cache/` und `result.json` sind lokal und nicht versioniert.

## TODOs

### Config und Repo

- [x] `config.yaml` gitignoren, `config.example.yaml` mit Platzhaltern committen
- [ ] `countries` nutzen oder entfernen; Nationen aus der Config lesen (`GER` statt Hardcode)
- [ ] optionale Keys: Cache-TTL, Output-Pfad, Request-Delay
- [ ] Reiter/Pferde aktivierbar machen, statt auskommentierter Listen

### Robustheit

- [ ] Request-Timeouts und Weiterlaufen, wenn ein Event fehlschlägt
- [ ] Encoding überall auf UTF-8
- [ ] `verify=False` entfernen oder dokumentieren, warum TLS deaktiviert ist
- [ ] Cache aufräumen (aktuell wächst `.cache/` unbegrenzt)
- [ ] Parser-Null-Checks (`evt_locator`, fehlende Links)

### Matching

- [ ] Pferdenamen nicht pauschal um die Startnummer kürzen (`Diamond 110` → `diamond`)
- [ ] Initiale-Match optional (sonst trifft `L. Scharrer` auch Laura Scharrer)
- [ ] Config-Namen als Anzeige behalten, nicht `str.title()`
- [ ] Tests für `normalize_name`, `rider_matches`, `normalize_horse`

### Ausgabe und CLI

- [ ] Einheitliche Event-Labels (Ort/Datum strippen, gleiches Format für Reiter und Pferde)
- [ ] Strukturierte JSON-Objekte statt zusammengebauter Strings
- [ ] CLI: `--config`, `--output`, `--no-cache`
- [ ] Kurz-Summary auf stdout, nicht nur `DONE`

### Aufräumen

- [ ] README (dieses File) pflegen
- [ ] `requirements.txt` mit `==` pinnen, `beautifulsoup4` statt `bs4`
- [ ] leeres `src/` und `event_cache_testing.json` entfernen
- [ ] `main.py` in Module splitten (`fetch`, `parse`, `match`), wenn die Datei wächst
