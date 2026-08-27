import hashlib
import random
import threading
import time

import requests
from pathlib import Path
from urllib.parse import urljoin
from urllib3.exceptions import InsecureRequestWarning

requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept-Language": "de-DE,de;q=0.9",
}
MAX_IN_FLIGHT = 8
REQUEST_DELAY = (0.2, 0.5)
REQUEST_TIMEOUT = 30

CACHE_DIR = Path(".cache")
CACHE_DIR.mkdir(exist_ok=True)
CACHE_HOURS = 6
# Empty /riders/ pages fill in later; don't keep them warm for hours.
EMPTY_RIDERS_CACHE_HOURS = 0.25

_http_slots = threading.Semaphore(MAX_IN_FLIGHT)
_thread_local = threading.local()


def apply_settings(
    *,
    cache_hours: float | None = None,
    empty_riders_cache_hours: float | None = None,
    request_delay: tuple[float, float] | None = None,
    max_in_flight: int | None = None,
    request_timeout: int | None = None,
) -> None:
    """Update runtime HTTP/cache knobs (called from settings.apply_settings)."""
    global CACHE_HOURS, EMPTY_RIDERS_CACHE_HOURS, REQUEST_DELAY
    global MAX_IN_FLIGHT, REQUEST_TIMEOUT, _http_slots

    if cache_hours is not None:
        CACHE_HOURS = cache_hours
    if empty_riders_cache_hours is not None:
        EMPTY_RIDERS_CACHE_HOURS = empty_riders_cache_hours
    if request_delay is not None:
        REQUEST_DELAY = request_delay
    if request_timeout is not None:
        REQUEST_TIMEOUT = request_timeout
    if max_in_flight is not None and max_in_flight != MAX_IN_FLIGHT:
        MAX_IN_FLIGHT = max_in_flight
        _http_slots = threading.Semaphore(MAX_IN_FLIGHT)


def get_http_session() -> requests.Session:
    """One Session per thread so Keep-Alive works safely with parallel fetches."""
    session = getattr(_thread_local, "session", None)
    if session is None:
        session = requests.Session()
        session.headers.update(HEADERS)
        # results.equi-score.com sends an incomplete cert chain; strict verify fails.
        session.verify = False
        _thread_local.session = session
    return session


def is_fresh(path, hours=CACHE_HOURS):
    age = time.time() - path.stat().st_mtime
    return age < hours * 3600


def cache_path(url: str) -> Path:
    h = hashlib.md5(url.encode()).hexdigest()
    return CACHE_DIR / f"{h}.html"


def looks_like_empty_riders_page(html: str) -> bool:
    return "rider_name" not in html


def fetch(url: str, use_cache=True) -> str:
    path = cache_path(url)

    if use_cache and path.exists():
        cached = path.read_text(encoding="utf-8")
        hours = CACHE_HOURS
        if "/riders/" in url and looks_like_empty_riders_page(cached):
            hours = EMPTY_RIDERS_CACHE_HOURS
        if is_fresh(path, hours=hours):
            return cached

    with _http_slots:
        time.sleep(random.uniform(*REQUEST_DELAY))
        r = get_http_session().get(url, timeout=REQUEST_TIMEOUT)
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


def absolute_url(base_url: str, href: str) -> str:
    return prefer_german_url(urljoin(base_url, href))
