import requests
from bs4 import BeautifulSoup
from datetime import datetime
from zoneinfo import ZoneInfo
import re

TZ = ZoneInfo("Europe/Berlin")

BASE_URL = "https://www.magicpapa-shop.de"
LIST_URL = "https://www.magicpapa-shop.de/c/events"

# ---------------------------------------------------------
# Deutsche Monatsnamen
# ---------------------------------------------------------

GERMAN_MONTHS = {
    "januar": 1, "jan": 1,
    "februar": 2, "feb": 2,
    "märz": 3, "maerz": 3, "mrz": 3,
    "april": 4, "apr": 4,
    "mai": 5,
    "juni": 6, "jun": 6,
    "juli": 7, "jul": 7,
    "august": 8, "aug": 8,
    "september": 9, "sep": 9,
    "oktober": 10, "okt": 10,
    "november": 11, "nov": 11,
    "dezember": 12, "dez": 12,
}

# ---------------------------------------------------------
# Datum + Uhrzeit Parser
# ---------------------------------------------------------

def parse_date_from_text(text):
    text = text.lower()

    # 1) Titel-Format: "02. Mai 2026" oder "02 mai 2026"
    m = re.search(r"(\d{1,2})[.\s]+([a-zäöü]+)[\s.]+(\d{4})", text)
    if m:
        day, month_name, year = m.groups()
        month_name = month_name.lower()

        if month_name not in GERMAN_MONTHS:
            return None

        month = GERMAN_MONTHS[month_name]

        # Uhrzeit extrahieren
        t = re.search(r"(\d{1,2})[:.](\d{2})", text)
        if t:
            hour, minute = t.groups()
        else:
            hour, minute = "18", "00"

        return datetime(
            int(year), month, int(day),
            int(hour), int(minute),
            tzinfo=TZ
        )

    # 2) URL-Format: "02-mai-2026-start-10-00"
    m2 = re.search(r"(\d{1,2})-([a-zäöü]+)-(\d{4}).*?(\d{1,2})-(\d{2})", text)
    if m2:
        day, month_name, year, hour, minute = m2.groups()
        month_name = month_name.lower()

        if month_name not in GERMAN_MONTHS:
            return None

        month = GERMAN_MONTHS[month_name]

        return datetime(
            int(year), month, int(day),
            int(hour), int(minute),
            tzinfo=TZ
        )

    return None

# ---------------------------------------------------------
# Format-Erkennung
# ---------------------------------------------------------

def detect_format(title):
    title = title.lower()
    if "modern" in title:
        return "Modern"
    if "standard" in title:
        return "Standard"
    if "prerelease" in title or "sealed" in title or "limited" in title:
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
        url = BASE_URL + link_tag["href"].lstrip("/")

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
