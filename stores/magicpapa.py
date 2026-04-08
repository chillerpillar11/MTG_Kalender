import requests
from bs4 import BeautifulSoup
from datetime import datetime
from zoneinfo import ZoneInfo
import re

TZ = ZoneInfo("Europe/Berlin")

BASE_URL = "https://www.magicpapa-shop.de"
LIST_URL = "https://www.magicpapa-shop.de/c/magic-turniere"

# ---------------------------------------------------------
# Hilfsfunktionen
# ---------------------------------------------------------

def parse_date_from_text(text):
    """
    Extrahiert Datum + Uhrzeit aus Titeln wie:
    - "SA 02. Mai 2026 Start 10:00"
    - "Freitag 17.April 18:00 Uhr"
    - "02-mai-2026-start-10-00"
    """

    # 1) Versuche deutsches Datum im Format "02. Mai 2026"
    m = re.search(r"(\d{1,2})[.\s]+([A-Za-zäöüÄÖÜ]+)[\s.]+(\d{4})", text)
    if m:
        day, month_name, year = m.groups()
        try:
            dt = datetime.strptime(f"{day} {month_name} {year}", "%d %B %Y")
        except:
            try:
                dt = datetime.strptime(f"{day} {month_name} {year}", "%d %b %Y")
            except:
                dt = None
    else:
        dt = None

    # 2) Uhrzeit extrahieren
    t = re.search(r"(\d{1,2})[:.](\d{2})", text)
    if t:
        hour, minute = t.groups()
    else:
        hour, minute = "18", "00"  # Fallback

    if dt:
        return dt.replace(hour=int(hour), minute=int(minute), tzinfo=TZ)

    # 3) Fallback: URL-Format "02-mai-2026-start-10-00"
    m2 = re.search(r"(\d{1,2})-([A-Za-zäöüÄÖÜ]+)-(\d{4}).*?(\d{1,2})-(\d{2})", text)
    if m2:
        day, month_name, year, hour, minute = m2.groups()
        try:
            dt = datetime.strptime(f"{day} {month_name} {year}", "%d %B %Y")
        except:
            dt = datetime.strptime(f"{day} {month_name} {year}", "%d %b %Y")
        return dt.replace(hour=int(hour), minute=int(minute), tzinfo=TZ)

    return None


def detect_format(title):
    title = title.lower()
    if "modern" in title:
        return "Modern"
    if "standard" in title:
        return "Standard"
    if "limited" in title or "sealed" in title or "prerelease" in title:
        return "Limited"
    return "Magic Event"


# ---------------------------------------------------------
# Hauptfunktion
# ---------------------------------------------------------

def fetch_magicpapa_events():
    events = []

    try:
        r = requests.get(LIST_URL, timeout=10)
        r.raise_for_status()
    except Exception as e:
        print("Magic Papa Fehler:", e)
        return events

    soup = BeautifulSoup(r.text, "html.parser")
    items = soup.select(".product-item")

    for item in items:
        title_tag = item.select_one(".product-item-title")
        link_tag = item.select_one("a.product-item-link")

        if not title_tag or not link_tag:
            continue

        title = title_tag.get_text(strip=True)
        url = BASE_URL + link_tag["href"]

        # Nur RCQs extrahieren
        if "rcq" not in title.lower():
            continue

        # Datum + Uhrzeit parsen
        dt = parse_date_from_text(title + " " + url)
        if not dt:
            print("⚠ Konnte Datum nicht parsen:", title)
            continue

        # Format bestimmen
        fmt = detect_format(title)

        events.append({
            "title": f"RCQ – {fmt}",
            "start": dt,
            "end": dt.replace(hour=dt.hour + 6),  # RCQs dauern lange
            "location": "Magic Papa, München",
            "url": url,
            "description": title,
            "all_day": False
        })

    return events
