import requests
from datetime import datetime
from zoneinfo import ZoneInfo

TZ = ZoneInfo("Europe/Berlin")

RACOON_URL = "https://racoon-rises.de/wp-json/tribe/events/v1/events"

LEGACY_KEYWORDS = [
    "legacy",
    "elm quali",
    "elm qualifier",
    "eternal",
    "eternal weekend",
    "ewk",
]

def detect_format(title: str):
    t = title.lower()

    # Legacy
    if any(k in t for k in LEGACY_KEYWORDS):
        return "Legacy"

    # Modern
    if "modern" in t:
        return "Modern"

    # Commander
    if "commander" in t or "edh" in t:
        return "Commander"

    # Draft / Sealed
    if "draft" in t:
        return "Draft"
    if "sealed" in t:
        return "Sealed"

    return "Unknown"


def normalize_title(title: str, fmt: str):
    t = title.lower()

    # Normalize ELM Qualifier
    if "elm" in t:
        return "Legacy Qualifier"

    return title


def fetch_racoon_events():
    events = []
    page = 1

    while True:
        resp = requests.get(RACOON_URL, params={"page": page})
        data = resp.json()

        for ev in data.get("events", []):
            title = ev["title"]
            fmt = detect_format(title)
            title = normalize_title(title, fmt)

            start = datetime.fromisoformat(ev["start_date"]).astimezone(TZ)
            end = datetime.fromisoformat(ev["end_date"]).astimezone(TZ)

            events.append({
                "title": f"Racoon – {title}",
                "format": fmt,
                "start": start,
                "end": end,
                "location": "Racoon Rises, München",
                "url": ev.get("url", ""),
                "description": ev.get("excerpt", ""),
                "all_day": False
            })

        if not data.get("next_rest_url"):
            break

        page += 1

    return events