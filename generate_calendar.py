import requests
from bs4 import BeautifulSoup
from datetime import datetime
from ics import Calendar, Event

# Wizards API: RCQs + Store Championships im Umkreis München
WIZARDS_URL = "https://locator.wizards.com/api/search?query=81547%20M%C3%BCnchen-Untergiesing-Harlaching,%20Deutschland&distance=100&searchType=magic-events&tag=regional_championship_qualifier&tag=store_championship&sort=date&sortDirection=Asc&page=1"

# MTGO Update Seite
MTGO_URL = "https://mtgoupdate.com/"

def fetch_wizards_events():
    events = []
    resp = requests.get(WIZARDS_URL)
    resp.raise_for_status()
    data = resp.json()

    for item in data.get("results", []):
        title = item.get("title")
        start = item.get("startDate")
        store = item.get("store", {}).get("name", "")
        address = item.get("store", {}).get("address", "")

        if not start:
            continue

        start_dt = datetime.fromisoformat(start.replace("Z", "+00:00"))

        e = Event()
        e.name = f"{title} – {store}"
        e.begin = start_dt
        e.location = address
        e.description = "WPN Event (RCQ oder Store Championship)"
        events.append(e)

    return events

def fetch_mtgo_events():
    events = []
    resp = requests.get(MTGO_URL)
    resp.raise_for_status()
    html = resp.text
    soup = BeautifulSoup(html, "html.parser")

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

    return events

def generate_ics():
    cal = Calendar()

    for e in fetch_wizards_events():
        cal.events.add(e)

    for e in fetch_mtgo_events():
        cal.events.add(e)

    with open("magic.ics", "w", encoding="utf-8") as f:
        f.writelines(cal)

if __name__ == "__main__":
    generate_ics()