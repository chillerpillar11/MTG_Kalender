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
# Hilfsfunktion: Uhrzeit aus Titel extrahieren
# ---------------------------------------------------------
def extract_time_from_title(title: str):
    """
    Sucht nach Uhrzeiten wie:
    - 18.30
    - 18:30
    - 19 Uhr
    """
    title = title.lower()

    # 18:30 oder 18.30
    m = re.search(r"(\d{1,2})[:\.](\d{2})", title)
    if m:
        return int(m.group(1)), int(m.group(2))

    # 19 Uhr
    m = re.search(r"(\d{1,2})\s*uhr", title)
    if m:
        return int(m.group(1)), 0

    return None


# ---------------------------------------------------------
# Parser für Event-Liste (enthält Modern!)
# ---------------------------------------------------------
def fetch_dd_list_events():
    print("Hole Event-Liste von Deck & Dice...")

    url = "https://www.dd-munich.de/event-list"
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        resp = requests.get(url, headers=headers, timeout=20)
        resp.raise_for_status()
    except Exception as e:
        print("Fehler beim Laden der Event-Liste:", e)
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    events = []

    # Titel stehen in div.JsVhwR
    for title_el in soup.select("div.JsVhwR"):
        title = title_el.get_text(strip=True)

        # Filter anwenden
        if not is_modern_or_rcq(title):
            continue

        # Datum extrahieren (steht im data-hook)
        data_hook = title_el.get("data-hook", "")
        m = re.search(r"event-title-(.*)", data_hook)
        if not m:
            continue

        # Wir müssen das Datum aus dem DOM-Kontext holen:
        # Der Titel steht in einer Event-Karte, die das Datum enthält.
        card = title_el.find_parent("div", attrs={"data-hook": re.compile(r"event-card-")})
        if not card:
            continue

        date_el = card.select_one("time")
        if not date_el:
            continue

        date_str = date_el.get("datetime")
        try:
            base_date = datetime.fromisoformat(date_str.replace("Z", "+00:00")).astimezone(TZ)
        except:
            continue

        # Uhrzeit aus Titel extrahieren
        t = extract_time_from_title(title)
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
            "url": url,
            "description": "",
        })

    print(f"DD Munich Modern/RCQ Events (Event-Liste): {len(events)}")
    return events


# ---------------------------------------------------------
# Hauptfunktion: kombiniert Kalender + Event-Liste
# ---------------------------------------------------------
def fetch_dd_munich_events():
    print("Hole Events von Deck & Dice / DD Munich...")

    # Nur Event-Liste nutzen, da Kalender Modern oft nicht zeigt
    list_events = fetch_dd_list_events()

    print(f"DD Munich Modern/RCQ Events gefunden: {len(list_events)}")
    return list_events
