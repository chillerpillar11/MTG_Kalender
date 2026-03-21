import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import re

TZ = ZoneInfo("Europe/Berlin")

# ---------------------------------------------------------
# Nur relevante Events für BB-Spiele:
# - RCQ
# - Store Championship (alle Formate)
# ---------------------------------------------------------
def is_relevant_bb_event(title: str) -> bool:
    t = title.lower()

    include = [
        "rcq",
        "regional championship qualifier",
        "store championship",
        "championship",
    ]

    return any(x in t for x in include)


# ---------------------------------------------------------
# Datum + Uhrzeit extrahieren
# Beispiel: "20.03.2026 18:30"
# ---------------------------------------------------------
def parse_datetime(text: str):
    text = text.strip()

    m = re.match(r"(\d{1,2})\.(\d{1,2})\.(\d{4})\s+(\d{1,2}):(\d{2})", text)
    if m:
        day = int(m.group(1))
        month = int(m.group(2))
        year = int(m.group(3))
        hour = int(m.group(4))
        minute = int(m.group(5))
        start = datetime(year, month, day, hour, minute, tzinfo=TZ)
        end = start + timedelta(hours=3)
        return start, end

    return None, None


# ---------------------------------------------------------
# Events von BB-Spiele scrapen
# ---------------------------------------------------------
def fetch_bb_spiele_events():
    print("Hole Events von BB-Spiele...")

    url = "https://www.bb-spiele.de/events"
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        resp = requests.get(url, headers=headers, timeout=20)
        resp.raise_for_status()
    except Exception as e:
        print("Fehler bei BB-Spiele:", e)
        return []

    soup = BeautifulSoup(resp.text, "html.parser")

    # Alle bekannten Event-Selektoren von "The Events Calendar"
    selectors = [
        ".tribe-events-calendar-list__event",
        ".tribe-events-calendar-day__event",
        ".tribe-events-calendar-month__event",
        ".tribe-events-pro-week-grid__event",
        ".tribe-events-pro-map__event-card",
        ".tribe-events-pro-photo__event",
        ".tribe-events-calendar-latest-past__event",
        ".tribe-events-calendar-latest__event",
        ".tribe-events-event-card",  # neuere Versionen
    ]

    cards = []
    for sel in selectors:
        found = soup.select(sel)
        if found:
            print(f"Selector '{sel}' → {len(found)} Events gefunden")
            cards.extend(found)

    print(f"Gesamt gefundene Event-Cards: {len(cards)}")

    events = []

    for card in cards:
        # Titel
        title_el = (
            card.select_one(".tribe-events-calendar-list__event-title-link")
            or card.select_one(".tribe-events-event-title")
            or card.select_one("h3")
            or card.select_one("a")
        )

        # Datum
        date_el = (
            card.select_one(".tribe-events-calendar-list__event-datetime")
            or card.select_one(".tribe-event-date-start")
            or card.select_one(".tribe-events-event-datetime")
            or card.select_one(".tribe-events-event-date")
        )

        if not title_el or not date_el:
            continue

        title = title_el.get_text(strip=True)
        date_text = date_el.get_text(strip=True)

        print(f"  → Card: '{title}' | Datum: '{date_text}'")

        if not is_relevant_bb_event(title):
            print("    ✗ Filter: nicht relevant für BB-Spiele")
            continue

        start, end = parse_datetime(date_text)
        if not start:
            print("    ✗ Datum/Uhrzeit nicht erkannt")
            continue

        print("    ✓ Relevantes Event übernommen")

        events.append({
            "title": title,
            "start": start,
            "end": end,
            "location": "BB-Spiele München",
            "url": url,
            "description": "",
        })

    print(f"BB-Spiele relevante Events: {len(events)}")
    return events
