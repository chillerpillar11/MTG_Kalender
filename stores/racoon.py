import requests
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

TZ = ZoneInfo("Europe/Berlin")

WORKER_URL = "https://curly-frog-1c07.black-credit-b521.workers.dev/"


def _normalize_title(raw_title: str) -> str:
    """
    Normalisiert bestimmte Event-Namen, ohne das Schema zu ändern.
    Beispiel:
    - ELM / Qualifier / Eternal Weekend → "Legacy Qualifier"
    """
    t = raw_title.lower()

    if "elm" in t or "eternal weekend" in t or "ewk" in t:
        return "Legacy ELM Qualifier"

    return raw_title


def fetch_racoon_events():
    events = []

    now = datetime.now(TZ)
    one_year = now + timedelta(days=365)

    params = {
        "timeMin": now.isoformat(),
        "timeMax": one_year.isoformat(),
        "singleEvents": "true",
        "orderBy": "startTime",
        "maxResults": "2500",
        "showDeleted": "false",
    }

    try:
        response = requests.get(WORKER_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        print("Fehler beim Laden des Racoon-Workers:", e)
        return []

    for item in data.get("items", []):
        title = item.get("summary", "") or ""
        title_lower = title.lower()

        # Filter: RCQ, Monthly Legacy, ELM / Eternal Weekend
        if not (
            "rcq" in title_lower
            or "regional championship qualifier" in title_lower
            or "monthly legacy" in title_lower
            or "elm" in title_lower
            or "eternal weekend" in title_lower
            or "ewk" in title_lower
        ):
            continue

        start_info = item.get("start", {})
        end_info = item.get("end", {})

        if "dateTime" not in start_info or "dateTime" not in end_info:
            continue

        start_dt = datetime.fromisoformat(start_info["dateTime"]).astimezone(TZ)
        end_dt = datetime.fromisoformat(end_info["dateTime"]).astimezone(TZ)

        desc = item.get("description", "") or ""
        url = item.get("htmlLink", "") or ""

        normalized_title = _normalize_title(title)

        events.append({
            "title": normalized_title,   # kein Prefix hier, Schema bleibt wie vorher
            "start": start_dt,
            "end": end_dt,
            "location": "Racoon Rises, Ulm",
            "url": url,
            "description": desc,
            "all_day": False
        })

    return events
