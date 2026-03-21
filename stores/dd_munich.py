import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import re

TZ = ZoneInfo("Europe/Berlin")

# ---------------------------------------------------------
# Relevante Formate für Deck & Dice (Modern, Legacy, Premodern, RCQ)
# Mit robuster Regex-Erkennung für Friday Night Modern
# ---------------------------------------------------------
def is_relevant_dd_event(title: str) -> bool:
    t = title.lower()

    # --- 1) Friday Night Modern (14-tägig) ---
    # Erkennen ALLE Varianten von Friday Night Modern
    if re.search(r"friday\s+night\s+modern", t):
        return True

    # --- 2) Wöchentliche Formate ---
    weekly_patterns = [
        r"after\s+work\s+modern",
        r"after\s+work\s+legacy",
        r"after\s+work\s+premodern",
        r"\blegacy\b",
        r"\bpremodern\b",
        r"\bmodern\b",  # Modern allgemein
    ]

    for pattern in weekly_patterns:
        if re.search(pattern, t):
            return True

    # --- 3) RCQ ---
    rcq_patterns = [
        r"\brcq\b",
        r"regional championship qualifier",
        r"\bqualifier\b",
    ]

    for pattern in rcq_patterns:
        if re.search(pattern, t):
            return True

    # --- 4) Ausschlüsse ---
    exclude = [
        "commander", "edh", "draft", "sealed", "prerelease", "pre-release",
        "standard", "pauper", "booster", "casual", "painting", "workshop",
        "warhammer", "40k", "age of sigmar", "pokémon", "pokemon", "lorcana",
        "yu-gi-oh", "yugioh", "flesh and blood", "fab", "one piece",
        "star wars", "spearwars", "spear wars", "spearhead",
        "tabletop", "boardgame", "brettspiel",
    ]

    if any(x in t for x in exclude):
        return False

    return False


# ---------------------------------------------------------
# Uhrzeit extrahieren (falls wir sie mal aus Text brauchen)
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
# Monatsnamen normalisieren (Vollformen + Abkürzungen)
# ---------------------------------------------------------
def parse_month_name(name: str) -> int | None:
    n = name.lower().strip().replace(".", "")

    MONTHS = {
        "jan": 1, "januar": 1,
        "feb": 2, "februar": 2,
        "mär": 3, "maer": 3, "maerz": 3, "märz": 3,
        "mrz": 3,
        "apr": 4, "april": 4,
        "mai": 5,
        "jun": 6, "juni": 6,
        "jul": 7, "juli": 7,
        "aug": 8, "august": 8,
        "sep": 9, "sept": 9, "september": 9,
        "okt": 10, "oktober": 10,
        "nov": 11, "november": 11,
        "dez": 12, "dezember": 12,
    }

    return MONTHS.get(n)


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

        # Beispiele:
        # "20. März 2026, 18:30 – 23:00"
        # "03. Apr. 2026, 18:30 – 23:00"
        m = re.match(
            r"(\d{1,2})\.\s+([A-Za-zÄÖÜäöü\.]+)\s+(\d{4}),\s+(\d{1,2}:\d{2})",
            date_text
        )
        if not m:
            print("    ✗ Datum/Uhrzeit nicht erkannt (Regex-Mismatch)")
            continue

        day = int(m.group(1))
        month_name = m.group(2)
        year = int(m.group(3))
        time_str = m.group(4)

        month = parse_month_name(month_name)
        if not month:
            print(f"    ✗ Monatsname unbekannt: '{month_name}'")
            continue

        try:
            hour, minute = map(int, time_str.split(":"))
        except Exception:
            print(f"    ✗ Uhrzeit konnte nicht extrahiert werden: '{time_str}'")
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
