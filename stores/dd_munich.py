import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import re

TZ = ZoneInfo("Europe/Berlin")

# ---------------------------------------------------------
# Relevante Formate für Deck & Dice
# ---------------------------------------------------------
def is_relevant_dd_event(title: str) -> bool:
    title = title.lower()

    # Formate, die wir aufnehmen wollen
    include = [
        # Modern
        "modern",
        "fnm",
        "friday night magic",
        "friday night modern",
        "after work modern",

        # Legacy
        "legacy",
        "after work legacy",

        # Premodern
        "premodern",
        "after work premodern",

        # RCQ
        "rcq",
        "regional championship qualifier",
        "qualifier",
    ]

    # Formate, die wir NICHT wollen
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
# Uhrzeit extrahieren
# ---------------------------------------------------------
def extract_time(text: str):
    text = text.lower()

    m = re.search(r"(\d{1,2})[:\.](\d{2})", text)
    if m:
        return int(m.group(1)), int(m.group(2))

    m = re.search(r"(\d{1,2})\s*uhr", text)
    if m:
        return int(m.group(1)), 0

    return None


# ---------------------------------------------------------
# Events aus dem Wix Event Widget
# ---------------------------------------------------------
def fetch_widget_events(soup):
    print("\n--- DEBUG: Widget-Parsing ---")

    events = []
    cards = soup.select('[data-hook="events-card"]')
    print(f"Gefundene Event-Cards: {len(cards)}")

    for card in cards:
        title_el = card.select_one('[data-hook="title"]')
        date_el = card.select_one('[data-hook="date"]')

        if not title_el or not date_el:
            continue

        title = title_el.get_text(strip=True)
        date_text = date_el.get_text(strip=True)

        print(f"  → Card: '{title}' | Datum: '{date_text}'")

        if not is_relevant_dd_event(title):
            print("    ✗ Filter: nicht relevant")
            continue

        # Beispiel: "20. März 2026, 18:30 – 23:00"
        m = re.match(r"(\d{1,2})\. (\w+) (\d{4}), (\d{1,2}:\d{2})", date_text)
        if not m:
            print("    ✗ Datum/Uhrzeit nicht erkannt")
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
            print("    ✗ Monatsname unbekannt")
            continue

        month = MONTHS[month_name]

        try:
            hour, minute = map(int, time_str.split(":"))
        except:
            print("    ✗ Uhrzeit konnte nicht extrahiert werden")
            continue

        start = datetime(year, month, day, hour, minute, tzinfo=TZ)
        end = start + timedelta(hours=3)

        print("    ✓ Relevantes Event übernommen")

        events.append({
            "title": title,
            "start": start,
            "end": end,
            "location": "Deck & Dice Munich",
            "url": "https://www.dd-munich.de",
            "description": "",
        })

    print(f"Widget relevante Events: {len(events)}")
    return events


# ---------------------------------------------------------
# Hauptfunktion
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

    widget_events = fetch_widget_events(soup)

    # Doppelte Events vermeiden
    seen = set()
    final = []

    for ev in widget_events:
        key = (ev["title"], ev["start"])
        if key not in seen:
            seen.add(key)
            final.append(ev)

    print(f"\n--- DEBUG: FINAL ---")
    print(f"Gesamt relevante Events: {len(final)}")
    for ev in final:
        print(f"  ✓ {ev['title']} @ {ev['start']}")

    return final
