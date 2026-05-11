from database import get_face_risk


def calculate_risk(name: str) -> str:
    if name.strip().lower() == "unknown":
        return "High"

    risk_level = get_face_risk(name)
    if risk_level is None:
        return "Low"

    normalized = risk_level.strip().lower()
    if normalized == "medium":
        return "Medium"
    if normalized == "high":
        return "High"
    return "Low"
