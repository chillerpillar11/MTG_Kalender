import requests
from datetime import datetime
from ics import Calendar, Event

print("Script gestartet")

# Stabile Wizards-JSON-API (wird von der Webseite selbst genutzt)
WIZARDS_API = (
    "https://locator.wizards.com/api/event/search"
    "?query=München"
    "&distance=100"
    "&searchType=magic-events"
)

MTGO_URL = "https://mtgoupdate.com/"


def fetch_wizards_events():
    print("Hole Wizards Events (stabile JSON API)...")

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json",
    }

    try:
        resp = requests.get(WIZARDS_API, headers=headers)
        data = resp.json()
    except Exception as e:
        print("Fehler beim Laden der Wizards API:", e)
        return []

    events = []

    # Die API liefert eine Liste unter "results"
    results = data.get("results", [])

    for item in results:
        title = item.get("title")
        store = item.get("storeName", "")
        address = item.get("address", "")
        start = item.get("startDate")

        if not (title and start):
            continue

        # Beispiel: "2026-04-12T14:00:00"
        try:
            dt = datetime.fromisoformat(start.replace("Z", ""))
        except:
            continue

        e = Event()
        e.name = f"{title} – {store}" if store else title
        e.begin = dt
        e.location = address
        e.description = "WPN Event (JSON API)"

        events.append(e)

    print(f"Wizards Events gefunden: {len(events)}")
    return events


def fetch_mtgo_events():
    print("Hole MTGO Events...")

    events = []
    try:
        resp = requests.get(MTGO_URL)
    except Exception as e:
        print("Fehler beim Laden von MTGO:", e)
        return events

    from bs4 import BeautifulSoup
    soup = BeautifulSoup(resp.text, "html.parser")

    rows = soup.select("table tbody tr")
    for row in rows:
        cols = [c.get_text(strip=True) for c in row.find_all("td")]
        if len(cols) < 4:
            continue

        name, format_, date_str, time_str = cols[:4]

        if "Modern" not in format_:
            continue

        dt_str = f"{date_str} {time_str}"
        try:
            start_dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M")
        except ValueError:
            continue

        e = Event()
        e.name = f"MTGO {name} ({format_})"
        e.begin = start_dt
        e.description = "MTGO Modern Event"
        events.append(e)

    print(f"MTGO Events gefunden: {len(events)}")
    return events


def generate_ics():
    print("Erzeuge Kalender...")

    cal = Calendar()

    wizards = fetch_wizards_events()
    mtgo = fetch_mtgo_events()

    print("Wizards Events:", len(wizards))
    print("MTGO Events:", len(mtgo))

    for e in wizards:
        cal.events.add(e)

    for e in mtgo:
        cal.events.add(e)

    print("Schreibe magic.ics...")
    with open("magic.ics", "w", encoding="utf-8") as f:
        f.writelines(cal)

    print("Fertig! Datei erzeugt.")


if __name__ == "__main__":
    generate_ics()
