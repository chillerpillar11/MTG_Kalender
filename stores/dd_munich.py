import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import re

TZ = ZoneInfo("Europe/Berlin")

# ---------------------------------------------------------
# Modern/RCQ Filter
# ---------------------------------------------------------
def is_modern_or_rcq(title: str) -> bool:
    title = title.lower()

    include = [
        "modern",
        "rcq",
        "regional championship qualifier",
        "qualifier",
    ]

    exclude = [
        "commander",
        "edh",
        "draft",
        "sealed",
        "prerelease",
        "pre-release",
        "standard",
        "pauper",
        "booster",
        "casual",
        "painting",
        "workshop",
        "warhammer",
        "40k",
        "age of sigmar",
        "pokémon",
        "pokemon",
        "lorcana",
        "yu-gi-oh",
        "yugioh",
        "flesh and blood",
        "fab",
        "one piece",
        "star wars",
        "spearwars",
        "spear wars",
        "spearhead",
        "tabletop",
        "boardgame",
        "brettspiel",
    ]

    if any(x in title for x in exclude):
        return False

    return any(x in title for x in include)


# ---------------------------------------------------------
# Hilfsfunktion: Uhrzeit aus Text extrahieren
# ---------------------------------------------------------
def extract_time(text: str):
    text = text.lower()

    # 18:30 oder 18.30
    m = re.search(r"(\d{1,2})[:\.](\d{2})", text)
    if m:
        return int(m.group(1)), int(m.group(2))

    # 19 Uhr
    m = re.search(r"(\d{1,2})\s*uhr", text)
    if m:
        return int(m.group(1)), 0

    return None


# ---------------------------------------------------------
# A) Modern-Events aus dem Monatskalender
# ---------------------------------------------------------
def fetch_calendar_modern_events(soup):
    events = []

    # Jede Kalenderzelle
    for cell in soup.select('[data-hook^="calendar-cell-"]'):
        data_hook = cell.get("data-hook", "")

        # Datum extrahieren
        m = re.search(r"calendar-cell-(\d{4})-(\d{2})-(\d{2})T", data_hook)
        if not m:
            continue

        year, month, day = map(int, m.groups())
        base_date = datetime(year, month, day, tzinfo=TZ)

        # Modern-Events stehen in <li class="nJOvU6">
        for li in cell.select("li.nJOvU6"):
            title_el = li.select_one(".JsVhwR")
            time_el = li.select_one(".KOi6Xx")

            if not title_el or not time_el:
                continue

            title = title_el.get_text(strip=True)
            time_text = time_el.get_text(strip=True)

            if not is_modern_or_rcq(title):
                continue

            t = extract_time(time_text)
            if not t:
                continue

            hour, minute = t
            start = base_date.replace(hour=hour, minute=minute)
            end = start + timedelta(hours=3)

            events.append({
                "title": title,
                "start": start,
                "end": end,
                "location": "Deck & Dice Munich",
                "url": "https://www.dd-munich.de",
                "description": "",
            })

    return events


# ---------------------------------------------------------
# B) Modern-Events aus dem Wix Event Widget
# ---------------------------------------------------------
def fetch_widget_modern_events(soup):
    events = []

    for card in soup.select('[data-hook="events-card"]'):
        title_el = card.select_one('[data-hook="title"]')
        date_el = card.select_one('[data-hook="date"]')

        if not title_el or not date_el:
            continue

        title = title_el.get_text(strip=True)
        date_text = date_el.get_text(strip=True)

        if not is_modern_or_rcq(title):
            continue

        # Beispiel: "20. März 2026, 18:30 – 23:00"
        m = re.match(r"(\d{1,2})\. (\w+) (\d{4}), (\d{1,2}:\d{2})", date_text)
        if not m:
            continue

        day = int(m.group(1))
        month_name = m.group(2).lower()
        year = int(m.group(3))
        time_str = m.group(4)

        MONTHS = {
            "januar": 1, "februar": 2, "märz": 3, "april": 4, "mai": 5, "juni": 6,
            "juli": 7, "august": 8, "september": 9, "oktober": 10, "november": 11, "dezember": 12
        }

        if month_name not in MONTHS:
            continue

        month = MONTHS[month_name]

        try:
            hour, minute = map(int, time_str.split(":"))
        except:
            continue

        start = datetime(year, month, day, hour, minute, tzinfo=TZ)
        end = start + timedelta(hours=3)

        events.append({
            "title": title,
            "start": start,
            "end": end,
            "location": "Deck & Dice Munich",
            "url": "https://www.dd-munich.de",
            "description": "",
        })

    return events


# ---------------------------------------------------------
# Hauptfunktion: kombiniert beide Quellen
# ---------------------------------------------------------
def fetch_dd_munich_events():
    print("Hole Events von Deck & Dice / DD Munich...")

    url = "https://www.dd-munich.de/event-list"
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        resp = requests.get(url, headers=headers, timeout=20)
        resp.raise_for_status()
    except Exception as e:
        print("Fehler bei DD Munich:", e)
        return []

    soup = BeautifulSoup(resp.text, "html.parser")

    calendar_events = fetch_calendar_modern_events(soup)
    widget_events = fetch_widget_modern_events(soup)

    # Doppelte Events vermeiden (Titel + Datum)
    seen = set()
    final = []

    for ev in calendar_events + widget_events:
        key = (ev["title"], ev["start"])
        if key not in seen:
            seen.add(key)
            final.append(ev)

    print(f"DD Munich Modern/RCQ Events gefunden: {len(final)}")
    return final
