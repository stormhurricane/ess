"""Technical scraper settings (separate from search config.yaml)."""

from __future__ import annotations

import json
from pathlib import Path

SETTINGS_PATH = "settings.json"

# Defaults match the previous hard-coded CLI behaviour.
DEFAULTS: dict = {
    "cache_hours": 6.0,
    "empty_riders_cache_hours": 0.25,
    "request_delay_min": 0.2,
    "request_delay_max": 0.5,
    "request_timeout": 30,
    "max_in_flight": 8,
    "event_workers": 4,
    "fetch_workers": 6,
    "output": "result.json",
    "cache_max_age_days": 14,
}

# Upper caps so UI/settings cannot hammer equi-score or burn Actions minutes.
MAX: dict = {
    "cache_hours": 168.0,  # 1 week
    "empty_riders_cache_hours": 24.0,
    "request_delay_min": 10.0,
    "request_delay_max": 10.0,
    "request_timeout": 120,
    "max_in_flight": 16,
    "event_workers": 8,
    "fetch_workers": 12,
    "cache_max_age_days": 90,
}

MIN: dict = {
    "cache_hours": 0.0,
    "empty_riders_cache_hours": 0.0,
    "request_delay_min": 0.0,
    "request_delay_max": 0.0,
    "request_timeout": 5,
    "max_in_flight": 1,
    "event_workers": 1,
    "fetch_workers": 1,
    "cache_max_age_days": 0,
}


def _clamp_number(key: str, value) -> float | int:
    lo = MIN[key]
    hi = MAX[key]
    try:
        num = float(value)
    except (TypeError, ValueError):
        num = float(DEFAULTS[key])
    num = max(float(lo), min(float(hi), num))
    if isinstance(DEFAULTS[key], int):
        return int(round(num))
    return num


def normalize_settings(raw: dict | None) -> dict:
    """Merge raw settings with defaults and clamp to min/max."""
    raw = raw or {}
    out = dict(DEFAULTS)

    for key in (
        "cache_hours",
        "empty_riders_cache_hours",
        "request_delay_min",
        "request_delay_max",
        "request_timeout",
        "max_in_flight",
        "event_workers",
        "fetch_workers",
        "cache_max_age_days",
    ):
        if key in raw and raw[key] is not None:
            out[key] = _clamp_number(key, raw[key])

    if "output" in raw and raw["output"]:
        path = str(raw["output"]).strip()
        out["output"] = path or DEFAULTS["output"]

    # Keep delay range ordered.
    if out["request_delay_min"] > out["request_delay_max"]:
        out["request_delay_min"], out["request_delay_max"] = (
            out["request_delay_max"],
            out["request_delay_min"],
        )

    return out


def load_settings(path: str | Path = SETTINGS_PATH) -> dict:
    """Load settings.json if present; otherwise defaults. Always clamped."""
    path = Path(path)
    if not path.exists():
        return normalize_settings(None)
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return normalize_settings(None)
    if not isinstance(raw, dict):
        return normalize_settings(None)
    return normalize_settings(raw)


def apply_settings(settings: dict, *, use_cache: bool = True) -> None:
    """Push runtime values into fetch / starters modules."""
    import fetch
    import starters

    fetch.apply_settings(
        cache_hours=settings["cache_hours"],
        empty_riders_cache_hours=settings["empty_riders_cache_hours"],
        request_delay=(settings["request_delay_min"], settings["request_delay_max"]),
        max_in_flight=settings["max_in_flight"],
        request_timeout=settings["request_timeout"],
        use_cache=use_cache,
    )
    starters.apply_settings(fetch_workers=settings["fetch_workers"])
