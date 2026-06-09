from database import get_face_risk

# In-memory cache: name -> "Low" | "Medium" | "High"
# Eliminates a SQLite read on every recognition frame for known faces.
# Invalidated whenever the DB changes (enroll, remove, risk update).
_risk_cache: dict = {}


def invalidate_risk_cache(name: str = None) -> None:
    """Remove one entry (or clear all) when the DB changes."""
    if name is None:
        _risk_cache.clear()
    else:
        _risk_cache.pop(name, None)


def calculate_risk(name: str) -> str:
    if name.strip().lower() == "unknown":
        return "High"

    if name in _risk_cache:
        return _risk_cache[name]

    risk_level = get_face_risk(name)
    if risk_level is None:
        return "High"

    normalized = risk_level.strip().lower()
    result = "Medium" if normalized == "medium" else "High" if normalized == "high" else "Low"
    _risk_cache[name] = result
    return result
