import requests
from bs4 import BeautifulSoup
from datetime import datetime
from zoneinfo import ZoneInfo

TZ = ZoneInfo("Europe/Berlin")

BASE_URL = "https://racoon-rises.com/pages/events"


def fetch_racoon_events():
    events = []

    try:
        response = requests.get(BASE_URL, timeout=10)
        response.raise_for_status()
    except Exception as e:
        print("Fehler beim Laden der Racoon-Rises-Seite:", e)
        return []

    soup = BeautifulSoup(response.text, "html.parser")

    # Jeder Tag ist ein Block
    day_blocks = soup.select(".day")

    for day in day_blocks:
        # Datum extrahieren
        date_tag = day.select_one(".day-title")
        if not date_tag:
            continue

        date_text = date_tag.get_text(strip=True)  # z.B. "27. April 2026"
        try:
            date_obj = datetime.strptime(date_text, "%d. %B %Y").date()
        except:
            continue

        # Events des Tages
        event_blocks = day.select(".ev")

        for ev in event_blocks:
            title_tag = ev.select_one(".ev-title")
            if not title_tag:
                continue

            title_raw = title_tag.get_text(strip=True)

            title_lower = title_raw.lower()

            # ⭐ Filter: Nur RCQs oder Monthly Legacy
            if not (
                "rcq" in title_lower
                or "regional championship qualifier" in title_lower
                or "monthly legacy" in title_lower
            ):
                continue

            # Zeit extrahieren
            time_tag = ev.select_one(".ev-time")
            if not time_tag:
                continue

            time_text = time_tag.get_text(strip=True)  # z.B. "11:00 – 18:00"
            try:
                start_str, end_str = [t.strip() for t in time_text.split("–")]
            except:
                continue

            # Datetime bauen
            try:
                start_dt = datetime.strptime(
                    f"{date_obj} {start_str}", "%Y-%m-%d %H:%M"
                ).replace(tzinfo=TZ)

                end_dt = datetime.strptime(
                    f"{date_obj} {end_str}", "%Y-%m-%d %H:%M"
                ).replace(tzinfo=TZ)
            except:
                continue

            # URL extrahieren (falls vorhanden)
            cta = ev.select_one(".ev-cta a")
            url = cta.get("href") if cta else ""

            # Beschreibung (optional)
            desc = ""
            if "rcq" in title_lower:
                desc = "Regional Championship Qualifier"
            elif "monthly legacy" in title_lower:
                desc = "Monthly Legacy Event"

            events.append({
                "title": f"Racoon Rises – {title_raw}",
                "start": start_dt,
                "end": end_dt,
                "location": "Racoon Rises, München",
                "url": url,
                "description": desc,
                "all_day": False
            })

    return events
