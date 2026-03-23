import requests
from bs4 import BeautifulSoup
from datetime import datetime

URL = "https://www.fanfinity.gg/magic-the-gathering/"

def fetch_fanfinity_events():
    events = []

    try:
        response = requests.get(URL, timeout=10)
        response.raise_for_status()
    except Exception as e:
        print("Fanfinity Fehler:", e)
        return events

    soup = BeautifulSoup(response.text, "html.parser")

    # Jeder Event ist ein Elementor Loop Item
    items = soup.select('div[data-elementor-type="loop-item"]')

    print(f"Fanfinity: Gefundene Loop-Items: {len(items)}")

    for item in items:
        # Titel
        title_tag = item.select_one("h1.elementor-heading-title a, h2.elementor-heading-title a")
        if not title_tag:
            continue

        title = title_tag.text.strip()
        url = title_tag["href"]

        # Alle Datumselemente holen
        date_tags = item.select(".elementor-post-info__item--type-custom")

        if len(date_tags) < 2:
            continue

        # Das zweite Element ist das echte Datum
        date_text = date_tags[-1].text.strip()

        # Datum parsen (z. B. "May 2026")
        try:
            parsed_date = datetime.strptime(date_text, "%B %Y")
        except:
            print("Fanfinity: Konnte Datum nicht parsen:", date_text)
            continue

        # Start/Ende setzen
        start = parsed_date.replace(day=1, hour=9, minute=0)
        end = parsed_date.replace(day=1, hour=18, minute=0)

        events.append({
            "title": title,
            "url": url,
            "start": start,
            "end": end,
            "store": "Fanfinity",
            "location": "Online",
            "description": f"Event von Fanfinity: {title}\n{url}"
        })

    print(f"Fanfinity Events gefunden: {len(events)}")
    return events
