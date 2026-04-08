import requests
from bs4 import BeautifulSoup
from datetime import datetime
from zoneinfo import ZoneInfo
import re

TZ = ZoneInfo("Europe/Berlin")

BASE_URL = "https://www.datefix.de"
PAGE_URL = "https://www.datefix.de/kalender/5800?dfxp={}"

def parse_time_range(text):
    text = text.lower()
    m = re.search(r"(\d{1,2}):(\d{2}).*?(\d{1,2}):(\d{2})", text)
    if m:
        sh, sm, eh, em = m.groups()
        return int(sh), int(sm), int(eh), int(em)

    m2 = re.search(r"(\d{1,2}):(\d{2})", text)
    if m2:
        sh, sm = m2.groups()
        return int(sh), int(sm), int(sh) + 6, int(sm)

    return None

def detect_format(title):
    t = title.lower()
    if "modern" in t:
        return "Modern"
    if "pioneer" in t:
        return "Pioneer"
    if "standard" in t:
        return "Standard"
    if "sealed" in t or "draft" in t or "limited" in t:
        return "Limited"
    return "Magic Event"

def fetch_gamesisland_events():
    events = []

    # Seiten 1–5 scrapen
    for page in range(1, 6):
        url = PAGE_URL.format(page)

        try:
            r = requests.get(url, timeout=10, headers={
                "User-Agent": "Mozilla/5.0"
            })
            r.raise_for_status()
        except Exception as e:
            print("Games Island Fehler:", e)
            continue

        soup = BeautifulSoup(r.text, "html.parser")

        # WICHTIG: Datefix liefert KEIN itemtype → wir müssen .terminitem scrapen
        items = soup.select(".terminitem")

        if not items:
            break

        for item in items:
            title_tag = item.select_one("h5[itemprop='name']")
            start_meta = item.select_one("meta[itemprop='startDate']")
            time_text = item.select_one(".dfx-zeit-liste-dreizeilig")
            location_tag = item.select_one("[itemprop='location'] [itemprop='name']")
            link_tag = item.select_one("a[href]")

            if not title_tag or not start_meta:
                continue

            title = title_tag.get_text(strip=True)
            lowered = title.lower()

            # Nur RCQ / Destination Qualifier / DQ
            if not (
                "rcq" in lowered
                or "destination qualifier" in lowered
                or "regional championship qualifier" in lowered
                or re.search(r"\bdq\b", lowered)
            ):
                continue

            start_dt = datetime.fromisoformat(start_meta["content"]).replace(tzinfo=TZ)

            if time_text:
                parsed = parse_time_range(time_text.get_text())
            else:
                parsed = None

            if parsed:
                sh, sm, eh, em = parsed
                end_dt = start_dt.replace(hour=eh, minute=em)
            else:
                end_dt = start_dt.replace(hour=start_dt.hour + 6)

            url = link_tag["href"]
            if url.startswith("/"):
                url = BASE_URL + url

            location = location_tag.get_text(strip=True) if location_tag else "Games Island"

            fmt = detect_format(title)

            events.append({
                "title": f"RCQ – {fmt}",
                "start": start_dt,
                "end": end_dt,
                "location": location,
                "url": url,
                "description": title,
                "all_day": False
            })

    return events
