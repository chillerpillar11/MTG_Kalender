import requests
from datetime import datetime
from zoneinfo import ZoneInfo

TZ = ZoneInfo("Europe/Berlin")

MTGO_URL = "https://www.mtgo.com/calendar.ics?format=Modern"


def parse_ics_datetime(value: str) -> datetime:
    """
    Parses ICS datetime strings like:
    - 20260412T110000Z
    - 20260412T110000
    """
    value = value.strip()

    # UTC with Z
    if value.endswith("Z"):
        return datetime.strptime(value, "%Y%m%dT%H%M%SZ").replace(tzinfo=TZ)

    # Local time (rare)
    return datetime.strptime(value, "%Y%m%dT%H%M%S").replace(tzinfo=TZ)


def fetch_mtgo_events():
    try:
        response = requests.get(MTGO_URL, timeout=10)
        response.raise_for_status()
        ics = response.text
    except Exception as e:
        print("Fehler beim Laden des MTGO ICS:", e)
        return []

    events = []
    current = {}
    in_event = False

    for line in ics.splitlines():
        line = line.strip()

        if line == "BEGIN:VEVENT":
            in_event = True
            current = {}
            continue

        if line == "END:VEVENT":
            in_event = False

            # Only Modern events (the feed is already filtered, but just in case)
            title = current.get("SUMMARY", "")
            if "modern" not in title.lower():
                continue

            # Build event
            events.append({
                "title": title,
                "start": current["DTSTART"],
                "end": current["DTEND"],
                "location": "MTGO",
                "url": current.get("URL", ""),
                "description": current.get("DESCRIPTION", ""),
                "all_day": False
            })
            continue

        if not in_event:
            continue

        # ICS fields
        if line.startswith("SUMMARY:"):
            current["SUMMARY"] = line[len("SUMMARY:"):].strip()

        elif line.startswith("DTSTART"):
            _, value = line.split(":", 1)
            current["DTSTART"] = parse_ics_datetime(value)

        elif line.startswith("DTEND"):
            _, value = line.split(":", 1)
            current["DTEND"] = parse_ics_datetime(value)

        elif line.startswith("DESCRIPTION:"):
            current["DESCRIPTION"] = line[len("DESCRIPTION:"):].strip()

        elif line.startswith("URL:"):
            current["URL"] = line[len("URL:"):].strip()

    return events
