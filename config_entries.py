"""Helpers for search config entries (riders / horses)."""


def entry_name(entry) -> str | None:
    """Plain string or mapping with name/title; empty → None."""
    if isinstance(entry, str):
        name = entry.strip()
        return name or None
    if isinstance(entry, dict):
        name = entry.get("name") or entry.get("title") or ""
        name = str(name).strip()
        return name or None
    return None


def entry_is_active(entry) -> bool:
    """Missing active → True (backwards compatible)."""
    if isinstance(entry, str):
        return True
    if isinstance(entry, dict):
        if "active" not in entry or entry["active"] is None:
            return True
        return bool(entry["active"])
    return False


def active_names(entries) -> list[str]:
    """Names to search: only active entries, order preserved, duplicates kept once."""
    names, _ = active_search_entries(entries, lambda name: name)
    return names


def active_search_entries(entries, normalize_fn) -> tuple[list[str], dict[str, str]]:
    """Normalized names for matching and norm → original config display name."""
    if not entries:
        return [], {}
    seen: set[str] = set()
    names: list[str] = []
    display: dict[str, str] = {}
    for entry in entries:
        if not entry_is_active(entry):
            continue
        name = entry_name(entry)
        if not name or name in seen:
            continue
        seen.add(name)
        norm = normalize_fn(name)
        names.append(norm)
        display.setdefault(norm, name)
    return names, display
