import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import re

TZ = ZoneInfo("Europe/Berlin")

# ---------------------------------------------------------
# Modern-Filter (Premodern ausgeschlossen)
# ---------------------------------------------------------
def is_modern_event(title: str) -> bool:
    t = title.lower()

    if "premodern" in t:
        return False

    return "modern" in t


# ---------------------------------------------------------
# Hilfsfunktionen
# ---------------------------------------------------------
def parse_day_suffix(day_str: str) -> int:
    return int(re.sub(r"(st|nd|rd|th)$", "", day_str))


def parse_time_string(t: str):
    t = t.strip().lower()

    if t == "noon":
        return 12, 0
    if t == "midnight":
        return 0, 0

    m = re.match(r"(\d{1,2})(?::(\d{2}))?(am|pm)", t)
    if m:
        hour = int(m.group(1))
        minute = int(m.group(2)) if m.group(2) else 0
        ampm = m.group(3)

        if ampm == "pm" and hour != 12:
            hour += 12
        if ampm == "am" and hour == 12:
            hour = 0

        return hour, minute

    return None


def extract_event(text: str):
    parts = text.split(" ", 1)
    if len(parts) < 2:
        return None

    time_str = parts[0]
    title = parts[1].strip()

    tm = parse_time_string(time_str)
    if not tm:
        return None

    hour, minute = tm
    return hour, minute, title


# ---------------------------------------------------------
# Eine einzelne Woche scrapen
# ---------------------------------------------------------
def scrape_week(container, month, year):
    events = []

    for day_index in range(7):
        day_div = container.select_one(f"#day{day_index}")
        if not day_div:
            continue

        legend = day_div.select_one("legend span")
        if not legend:
            continue

        legend_text = legend.get_text(strip=True)
        m = re.match(r"[A-Za-z]+\s+(\d{1,2}[a-z]{2})", legend_text)
        if not m:
            continue

        day_number = parse_day_suffix(m.group(1))

        for font in day_div.select("font"):
            text = font.get_text(strip=True)
            parsed = extract_event(text)
            if not parsed:
                continue

            hour, minute, title = parsed

            # Modern-Filter
            if not is_modern_event(title):
                continue

            # Format-Tags
            t = title.lower()
            if "showcase" in t:
                tag = "[Showcase] "
            elif "prelim" in t:
                tag = "[Prelim] "
            elif "modern" in t:
                tag = "[Modern] "
            else:
                tag = ""

            final_title = f"{tag}MTGO – {title.strip()}"

            start = datetime(year, month, day_number, hour, minute, tzinfo=TZ)
            end = start + timedelta(hours=3)

            events.append({
                "title": final_title,
                "start": start,
                "end": end,
                "location": "Magic Online",
                "url": "https://mtgoupdate.com",
                "description": "",
            })

    return events


# ---------------------------------------------------------
# Hauptfunktion: ALLE Wochen scrapen
# ---------------------------------------------------------
def fetch_mtgo_events():
    print("Hole MTGO Events...")

    url = "https://mtgoupdate.com"
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        resp = requests.get(url, headers=headers, timeout=20)
        resp.raise_for_status()
    except Exception as e:
        print("Fehler bei MTGO:", e)
        return []

    soup = BeautifulSoup(resp.text, "html.parser")

    # Monat + Jahr stehen im <h1>
    header = soup.select_one("h1")
    if not header:
        return []

    header_text = header.get_text(strip=True)
    m2 = re.match(r"([A-Za-z]+)\s+(\d{4})", header_text)
    if not m2:
        return []

    month_name = m2.group(1)
    year = int(m2.group(2))
    month = datetime.strptime(month_name, "%B").month

    all_events = []

    # Alle Wochen sind im HTML → alle Container scrapen
    for week in range(0, 4):
        url = f"https://mtgoupdate.com/weekdata.php?week={week}"
        ...

    print(f"Gefundene Wochen: {len(containers)}")

    for idx, container in enumerate(containers):
        week_events = scrape_week(container, month, year)
        print(f"Woche {idx}: {len(week_events)} Modern-Events")
        all_events.extend(week_events)

    print(f"MTGO Modern Events gesamt: {len(all_events)}")
    return all_events
