# ESS — Equi-Score Scraper

**v1.1** — lokales CLI. GUI/Cloud-Ideen: Roadmap am Ende.

Sucht auf [equi-score.de](https://www.equi-score.de/) deutsche Turniere und prüft,
ob konfigurierte Reiter oder Pferde in den Starterlisten stehen.

Ergebnis: `result.json`.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp config.example.yaml config.yaml
cp settings.example.json settings.json   # optional
```

In `config.yaml` die zu suchenden Reiter und Pferde eintragen. Diese Datei ist
gitignored und gehört nicht ins Repo.

Technische Knöpfe (Cache, Parallelität, Delay) liegen optional in `settings.json`
(Vorlage: `cp settings.example.json settings.json`). Fehlt die Datei, gelten die
Defaults aus dem Code (Werte werden auf Min/Max begrenzt).

## Nutzung

```bash
python main.py
python main.py --config other.yaml --output woche.json --no-cache
```

| Flag | Wirkung |
| ---- | ------- |
| `--config PATH` | Such-Config (Default: `config.yaml`) |
| `--output PATH` | Ergebnis-JSON (überschreibt `settings.json` → `output`) |
| `--no-cache` | Cache nicht lesen; frische HTTP-Antworten (schreibt weiter nach `.cache/`) |

Das Skript:

1. lädt die Event-Übersicht aus dem Next.js-Payload (alle Wochen, nicht nur die ersten zwei im UI)
2. filtert nach Nation (`GER`) und Zeitfenster: **letztes Wochenende** (Vergangenheit) plus das **nächste Wochenende** (jeweils die ganze Kalenderwoche)
3. holt je Event die Starterliste (`/riders/`); ist die leer, die Klassen-`startlist`/`resultlist`-Seiten
4. gleicht Namen mit der Config ab
5. schreibt Treffer nach `result.json` und gibt eine Kurz-Summary auf stdout aus

Die öffentliche Startseite paginiert (`Load more`) und zeigt standardmäßig nur die aktuelle plus die letzte Kalenderwoche. Die Eventliste selbst steckt vollständig in der Seite — der Scraper liest diese Payload statt sichtbarer HTML-Karten.

Viele Turniere lassen `/riders/` leer; Reiter und Pferde stehen dann nur in den Prüfungs-Start-/Ergebnislisten. Der Scraper fällt in dem Fall darauf zurück (bevorzugt `startlist`).

HTTP-Antworten werden unter `.cache/` für 6 Stunden zwischengespeichert.
Leere `/riders/`-Seiten nur **15 Minuten** (Listen werden oft später nachgeliefert).
Requests laufen parallel (Events + Startlisten), begrenzt auf max. 8 gleichzeitige
Verbindungen, mit kurzer Pause (0,2–0,5 s) pro Netz-Request. Pro Worker-Thread
wird eine `requests.Session` mit Keep-Alive wiederverwendet.

**TLS:** Der Scraper setzt `verify=False`, weil `results.equi-score.com` (Events,
`/riders/`, Startlisten) eine **unvollständige Zertifikatskette** liefert —
Python bricht dann mit `CERTIFICATE_VERIFY_FAILED` ab. `www.equi-score.de`
verifyiert normal; der Fehler betrifft nur den Results-Host. Bis equi-score das
behebt, bleibt die Prüfung deaktiviert (nur öffentliche Starterlisten, kein Login).

## Konfiguration

Vorlage: `config.example.yaml`

```yaml
riders:
  - name: Max Mustermann
    active: true
  - name: Erika Musterfrau
    active: false

horses:
  - name: Epona
    active: true

nations:
  - GER
```

- **Reiter:** Nachname muss passen; Vorname exakt oder als Initiale (`L. Mustermann`).
- **Pferde:** Vergleich ohne Groß/Kleinschreibung. **Ohne** Nummer in der Config
(`Chili`) wird eine Startnummer auf der Liste ignoriert (`Chili 57`). **Mit** Nummer
in der Config (`Diamond 110`) muss exakt passen — kein pauschales Abschneiden.
- **Nationen:** Equi-score-Codes (`GER`). Fehlt der Key oder ist die Liste leer, gilt `GER`.
- **Aktiv:** Einträge als `{name, active}`. Nur `active: true` wird gesucht
(`active` fehlt → aktiv). Reine Strings (`- Max Mustermann`) gehen weiter.
Später GUI: Toggle = `active`, Löschen = Eintrag entfernen.



### Technische Settings (`settings.json`)

Getrennt von der Such-Config. Vorlage: `settings.example.json`.


| Key                                       | Default       | Min     | Max |
| ----------------------------------------- | ------------- | ------- | --- |
| `cache_hours`                             | 6             | 0       | 168 |
| `empty_riders_cache_hours`                | 0.25          | 0       | 24  |
| `request_delay_min` / `request_delay_max` | 0.2 / 0.5     | 0       | 10  |
| `request_timeout`                         | 30            | 5       | 120 |
| `max_in_flight`                           | 8             | 1       | 16  |
| `event_workers`                           | 4             | 1       | 8   |
| `fetch_workers`                           | 6             | 1       | 12  |
| `output`                                  | `result.json` | —       | —   |
| `cache_max_age_days`                      | 14            | 0 (aus) | 90  |


`cache_max_age_days`: Beim Start werden `.cache/*.html` gelöscht, die älter sind als X Tage
(nach Datei-`mtime`). `0` = Aufräumen aus.

## Ausgabe

`result.json` gruppiert Treffer nach Reiter und Pferd (Schlüssel = Schreibweise aus der Config).
Pro Treffer ein Objekt mit `location`, `date`, `url`:

```json
{
  "gefundene_reiter": {
    "Max Mustermann": [
      {
        "location": "Musterstadt",
        "date": "Sa 01.01.",
        "url": "https://results.equi-score.com/event/123/1/de"
      }
    ]
  },
  "gefundene_pferde": {}
}
```

`.cache/` und `result.json` sind lokal und nicht versioniert.

## TODOs



### Erledigt (Stand)

- [x] `config.yaml` gitignoren, `config.example.yaml` mit Platzhaltern
- [x] Eventliste aus Next.js-Payload statt DOM-Karten
- [x] Fallback: leere `/riders/` → Klassen-`startlist`/`resultlist`
- [x] Scope: letztes + nächstes Wochenende (Kalenderwochen)
- [x] Parallelität, kürzerer Delay, Keep-Alive-Session pro Thread
- [x] Leere `/riders/`-Seiten nur 15 min cachen
- [x] Request-Timeouts; einzelne Events/Listen bei Fehlern überspringen
- [x] UTF-8 für Cache und `result.json`
- [x] `event_cache_testing.json` entfernt



### Struktur / Refactoring

Nacheinander, jeweils ohne Verhaltensänderung (`python main.py` bleibt):

- [x] 1. `fetch.py` — HTTP, Cache, Session, Delay/Semaphore aus `main.py` ziehen
- [x] 2. `events.py` — Payload-Parse, Wochenend-Scope, `get_events`
- [x] 3. `starters.py` — `/riders/` + Startlisten-Fallback
- [x] 4. `match.py` — `normalize_*`, `rider_matches`
- [x] 5. `main.py` — nur Config laden, Events orchestrieren, Ergebnis schreiben
- [x] 6. leeres `src/` löschen



### Tests

- [x] Testdatei(en) für Matching (`normalize_name`, `rider_matches`, `normalize_horse`)
- [x] Tests für Wochenend-Scope (`weekend_scope_mondays`)
- [x] Optional: kleine HTML-Fixtures für Payload- und Startlisten-Parser



### Config

- [x] `countries` → `nations` mit Codes (`GER`); aus Config lesen, Default `GER`
- [x] optionale technische Settings in `settings.json` (Cache, Workers, Delay, Output; Min/Max)
- [x] Reiter/Pferde mit `active` (Toggle/Löschen-ready; Strings weiter erlaubt)



### Robustheit

- [x] `verify=False` dokumentiert (unvollständige Kette auf `results.equi-score.com`)
- [x] Cache aufräumen: `.cache/`-Dateien älter als `cache_max_age_days` (Default 14)
- [x] Parser-Null-Checks im DOM-Fallback (fehlende Elemente → skip, kein Crash)



### Matching

- [x] Pferdenamen: Startnummer nur streichen, wenn Config keine hat (`Chili` ja, `Diamond 110` nein)
- [x] Config-Namen als Anzeige behalten, nicht `str.title()`



### Ausgabe und CLI

- [x] Einheitliche Event-Labels (Ort/Datum strippen, gleiches Format für Reiter und Pferde)
- [x] Strukturierte JSON-Objekte statt zusammengebauter Strings
- [x] CLI: `--config`, `--output`, `--no-cache`
- [x] Kurz-Summary auf stdout, nicht nur `DONE`



### Aufräumen

- [x] `requirements.txt` mit `==` pinnen, `beautifulsoup4` statt `bs4`



## Roadmap — GUI / Cloud (nach v1.1)

CLI (`python main.py` + lokale `config.yaml`) bleibt. Web und Actions kommen **dazu**, nicht als Ersatz.

### Zielbild

Kleine **private Web-App** (Vercel): Config pflegen, letzte Treffer ansehen, Scrape per Knopf oder Cron anstoßen. Kein öffentlicher Index, keine Roh-HTML-Suche — nur das, was heute schon die CLI macht, aber ohne Terminal.

**Datenfluss:** GUI ↔ serverseitige API ↔ **privates** GitHub-Repo (`config.yaml`, `result.json`, optional `settings.json`). Der Scraper läuft in **GitHub Actions** (Cron + manuell), schreibt `result.json` ins Repo. Das Frontend liest/schreibt Config nur über die API (GitHub-Token nie im Browser).

**Auth:** Basic Auth vor der ganzen App („htpasswd“-Feeling) — reicht für wenige Nutzer.

**Bereits erledigt (CLI-Grundlage):** strukturiertes `result.json` (`location`, `date`, `url`), Config-Einträge mit `{name, active}` — GUI kann darauf aufsetzen.

**Architektur:** Scraper-Workflow in **`ess`** (public, Actions gratis) · Config/Result in **`ess-data`** (private) · GUI in **`web/`** (Vercel).

---

### Tasks (kleine Schritte)

Reihenfolge einhalten — jeder Punkt ist ein abgeschlossener Mini-Schritt.

#### A — Privates Daten-Repo

- [ ] GitHub-Repo `ess-data` anlegen (private)
- [ ] `config.yaml` aus `config.example.yaml` + Platzhalter-Namen anlegen
- [ ] Leeres `result.json` anlegen: `{"gefundene_reiter":{},"gefundene_pferde":{}}`
- [ ] Optional: `settings.json` aus `settings.example.json` (Cloud-Werte konservativ)

#### B — Repo `ess` public machen

Vor Block C — damit Actions-Läufe **kein** Minuten-Kontingent verbrauchen (`ess` ist derzeit **private**).

- [ ] Prüfen: keine `config.yaml`, `result.json`, `settings.json`, `.env` im Repo oder in der Git-History
- [ ] `.gitignore` und `*.example.*`-Vorlagen reichen; echte Daten nur lokal bzw. in `ess-data`
- [ ] GitHub: `stormhurricane/ess` → Settings → Change visibility → **public**
- [ ] Kurz verifizieren: Workflow-Tab sichtbar, kein Secret im Code

#### C — Token & Secrets

- [ ] Fine-grained PAT anlegen (nur Repo `ess-data`, Contents read/write)
- [ ] Secret `ESS_DATA_TOKEN` im **public** Repo `ess` hinterlegen
- [ ] Optional: Secret `ESS_DATA_REPO` = `stormhurricane/ess-data` (falls nicht hardcoded)

#### D — GitHub Action (Scrape, noch ohne GUI)

- [ ] `.github/workflows/scrape.yml` anlegen (Trigger: nur `workflow_dispatch` zuerst)
- [ ] Job: `runs-on: ubuntu-latest`
- [ ] Step: `ess`-Code checkout (Default)
- [ ] Step: `ess-data` checkout nach `./data` mit `ESS_DATA_TOKEN`
- [ ] Step: `pip install -r requirements.txt`
- [ ] Step: `python main.py --config data/config.yaml --output data/result.json`
- [ ] Step: Commit + Push nur wenn `result.json` geändert (`ESS_DATA_TOKEN`)
- [ ] Manuell testen: Actions → Run workflow → `result.json` in `ess-data` prüfen
- [ ] Optional: `actions/cache` für `.cache/` (schnellere Folgeläufe)
- [ ] Cron ergänzen (z. B. `0 6 * * *`) — erst wenn manueller Lauf stabil

#### E — Vercel-Grundgerüst (read-only)

- [ ] Ordner `web/` — Next.js App scaffolden
- [ ] Env in Vercel: `ESS_DATA_TOKEN`, `ESS_DATA_REPO`, Basic-Auth-User/Pass
- [ ] Middleware: Basic Auth auf allen Routen außer `/api/health` (optional)
- [ ] Vercel-Projekt mit Root `web/` verbinden

#### F — API read-only

- [ ] `GET /api/config` — GitHub Contents API → YAML parsen → JSON
- [ ] `GET /api/results` — GitHub Contents API → `result.json` parsen
- [ ] Fehlerfälle: 404, Token fehlt, ungültiges JSON → klare HTTP-Status

#### G — GUI read-only (erster sichtbarer Meilenstein)

- [ ] Layout/Navigation (Config | Treffer)
- [ ] Seite **Treffer:** Liste aus `GET /api/results`, Links klickbar
- [ ] Seite **Config:** Reiter/Pferde read-only anzeigen
- [ ] Leerzustände + Lade-/Fehleranzeige
- [ ] Deploy auf Vercel, End-to-End testen (Auth → Daten sichtbar)

#### H — Config schreiben

- [ ] `PUT /api/config` — JSON validieren, YAML bauen, GitHub Contents API Update (SHA!)
- [ ] Validierung: leere Namen, Duplikate abweisen
- [ ] Config-UI: Eintrag hinzufügen
- [ ] Config-UI: Toggle `active`
- [ ] Config-UI: Eintrag löschen
- [ ] Config-UI: `nations` bearbeiten
- [ ] Speichern mit Feedback (Loading, Erfolg, Fehler)

#### I — Scrape aus der GUI

- [ ] Fine-grained PAT oder `GITHUB_TOKEN`-Scope: Actions read/write auf **`ess`**
- [ ] Secret `ESS_WORKFLOW_TOKEN` in Vercel (falls anderer Token als `ESS_DATA_TOKEN`)
- [ ] `POST /api/scrape` — `workflow_dispatch` für `scrape.yml`
- [ ] `GET /api/scrape/status` — letzter Workflow-Lauf (Status, Zeit)
- [ ] UI: Button „Jetzt scrapen“ + Status/Spinner + Hinweis „Ergebnis in ~X Min“

#### J — Feinschliff

- [ ] API-Fehler im UI verständlich anzeigen
- [ ] README: Setup Abschnitt GUI/Cloud ergänzen
- [ ] Optional: reduzierte Settings-Seite (`settings.json` read/write)
- [ ] Optional: Responsives Layout nachziehen

---

### Phase-Übersicht (Referenz)

| Phase | Tasks | Ergebnis |
| ----- | ----- | -------- |
| **1** | A + B + C + D | `ess` public, Scrape in Actions, Result in `ess-data` |
| **2** | E + F + G | Web-App zeigt Config + Treffer (read-only) |
| **3** | H + I | Config editierbar, Scrape per Knopf |
| **4** | J | Polish |

---

### Bewusst später / nicht v1 GUI

- [ ] Öffentlicher Voll-Index aller Starterlisten (Frontend sucht ohne Crawl-Config)
- [ ] Cron-Ausdruck aus der UI ändern (Zeitplan bleibt in `scrape.yml`)
- [ ] Roh-`.cache/`-HTML dem Frontend zum Durchsuchen geben