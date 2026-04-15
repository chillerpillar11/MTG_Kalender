#!/usr/bin/env python3
import uuid
import json
import requests
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from pathlib import Path
from functools import lru_cache

# Stores importieren
from stores.bb_spiele import fetch_bb_spiele_events
from stores.funtainment import fetch_funtainment_events
from stores.dd_munich import fetch_dd_munich_events
from stores.fanfinity import fetch_fanfinity_events
from stores.countdown import fetch_countdown_events
from stores.racoon import fetch_racoon_events
from stores.magicpapa import fetch_magicpapa_events
from stores.gamesisland import fetch_gamesisland_events
from stores.mtgo import fetch_mtgo_events

TZ = ZoneInfo("Europe/Berlin")
HISTORY_FILE = Path("events_history.json")

# ---------------------------------------------------------
# Feiertage aus API laden (mit Cache)
# ---------------------------------------------------------
@lru_cache
def load_bavarian_holidays(year):
    url = f"https://date.nager.at/api/v3/PublicHolidays/{year}/DE"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        print("Fehler beim Laden der Feiertage:", e)
        return set()

    holidays = set()
    for entry in data:
        counties = entry.get("counties")
        if counties is None or "DE-BY" in counties:
            holidays.add(datetime.fromisoformat(entry["date"]).date())

    return holidays


# ---------------------------------------------------------
# ICS-Helfer
# ---------------------------------------------------------
def format_dt(dt: datetime) -> str:
    return dt.astimezone(TZ).strftime("%Y%m%dT%H%M%S")


def generate_ics(events, filename="magic.ics"):
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Magic Munich Calendar//DE",
        "CALSCALE:GREGORIAN",
        "X-WR-CALNAME:Minga Boys Magic Kalender",
        "X-WR-TIMEZONE:Europe/Berlin",
    ]

    now_str = format_dt(datetime.now(TZ))

    for ev in events:
        uid = f"{uuid.uuid4()}@magic-munich"

        lines.append("BEGIN:VEVENT")
        lines.append(f"UID:{uid}")
        lines.append(f"DTSTAMP:{now_str}")

        if ev.get("all_day"):
            lines.append(f"DTSTART;VALUE=DATE:{ev['start'].strftime('%Y%m%d')}")
            lines.append(f"DTEND;VALUE=DATE:{ev['end'].strftime('%Y%m%d')}")
        else:
            lines.append(f"DTSTART:{format_dt(ev['start'])}")
            lines.append(f"DTEND:{format_dt(ev['end'])}")

        lines.append(f"SUMMARY:{ev['title']}")
        lines.append(f"LOCATION:{ev.get('location', '')}")
        lines.append(f"URL:{ev.get('url', '')}")

        desc = ev.get("description", "").replace("\n", " ").replace("\r", " ")
        lines.append(f"DESCRIPTION:{desc}")

        lines.append("END:VEVENT")

    lines.append("END:VCALENDAR")
    Path(filename).write_text("\n".join(lines), encoding="utf-8")
    print(f"ICS erzeugt: {filename}")


# ---------------------------------------------------------
# Event-History laden/speichern
# ---------------------------------------------------------
def load_history():
    if HISTORY_FILE.exists():
        try:
            return json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
        except:
            return []
    return []


def save_history(events):
    serializable = [
        {
            "title": ev["title"],
            "start": ev["start"].isoformat(),
            "end": ev["end"].isoformat(),
            "location": ev.get("location", ""),
            "url": ev.get("url", ""),
            "description": ev.get("description", ""),
            "all_day": ev.get("all_day", False)
        }
        for ev in events
    ]
    HISTORY_FILE.write_text(json.dumps(serializable, indent=2), encoding="utf-8")


# ---------------------------------------------------------
# 🟩 Manuelle Events aus Telegram-Bot laden
# ---------------------------------------------------------
def load_manual_events():
    path = Path("manual_events.json")
    if not path.exists():
        return []

    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except:
        return []

    events = []
    for ev in raw:
        try:
            events.append({
                "title": ev["title"],
                "start": datetime.fromisoformat(ev["start"]),
                "end": datetime.fromisoformat(ev["end"]),
                "location": ev.get("location", ""),
                "url": ev.get("url", ""),
                "description": ev.get("description", ""),
                "all_day": ev.get("all_day", False),
                "source": "MANUAL"
            })
        except Exception as e:
            print("Fehler in manual_events.json:", e)

    return events


# ---------------------------------------------------------
# Proxy-Event-Generator
# ---------------------------------------------------------
def generate_proxy_events(event, events_by_date):
    title = event["title"].lower()

    if "rcq" in title or "regional championship qualifier" in title:
        return []

    weekly_formats = [
        "after work standard",
        "after work modern",
        "after work legacy",
        "after work premodern",
        "friday night modern",
        "friday night standard",
    ]

    if not any(f in title for f in weekly_formats):
        return []

    proxy_events = []

    start = event["start"]
    end = event["end"]
    delta = timedelta(weeks=1)

    holidays = load_bavarian_holidays(start.year) | load_bavarian_holidays(start.year + 1)
    year_end = datetime(start.year, 12, 31, tzinfo=TZ)

    next_start = start + delta
    next_end = end + delta

    while next_start <= year_end:

        if next_start.date() in events_by_date:
            next_start += delta
            next_end += delta
            continue

        if next_start.date() not in holidays:
            proxy_events.append({
                "title": event["title"],
                "start": next_start,
                "end": next_end,
                "location": event.get("location", ""),
                "url": ev.get("url", ""),
                "description": event.get("description", ""),
                "all_day": event.get("all_day", False)
            })

        next_start += delta
        next_end += delta

    return proxy_events


# ---------------------------------------------------------
# MAIN
# ---------------------------------------------------------
def main():
    print("Script gestartet")
    print("Erzeuge Kalender...")

    all_events = []

    stores = [
        ("BB-Spiele", fetch_bb_spiele_events, "BB-Spiele – "),
        ("Funtainment", fetch_funtainment_events, "Funtainment – "),
        ("Deck & Dice", fetch_dd_munich_events, "Deck & Dice – "),
        ("Fanfinity", fetch_fanfinity_events, "Fanfinity – "),
        ("Countdown Spielewelt", fetch_countdown_events, "Countdown – "),
        ("Racoon Rises", fetch_racoon_events, "Racoon Rises – "),
        ("Magic Papa", fetch_magicpapa_events, "Magic Papa – "),
        ("Games Island", fetch_gamesisland_events, "Games Island – "),
        ("MTGO", fetch_mtgo_events, "MTGO – "),
    ]

    for name, fetcher, prefix in stores:
        try:
            events = fetcher()
            print(f"{name}: {len(events)} Events gefunden")
            for ev in events:
                ev["title"] = f"{prefix}{ev['title']}"
                ev["source"] = name
            all_events.extend(events)
        except Exception as e:
            print(f"Fehler bei {name}: {e}")

    print(f"Neue Events geladen: {len(all_events)}")

    # 🟩 MTGO-Events ausblenden
    all_events = [e for e in all_events if e["source"] != "MTGO"]

    # 🟩 Manuelle Events aus Telegram-Bot hinzufügen
    manual_events = load_manual_events()
    print(f"Manuelle Events geladen: {len(manual_events)}")
    all_events.extend(manual_events)

    # Events nach Datum gruppieren
    events_by_date = {}
    for ev in all_events:
        d = ev["start"].date()
        events_by_date.setdefault(d, []).append(ev)

    # Proxy-Events erzeugen
    proxy_events = []
    for ev in all_events:
        proxy_events.extend(generate_proxy_events(ev, events_by_date))

    print(f"Erzeugte Proxy-Events: {len(proxy_events)}")

    # Alte Events laden
    history = load_history()

    restored = []
    if history:
        now = datetime.now(TZ).date()
        years = {now.year, now.year + 1}
        holidays = set()
        for y in years:
            holidays |= load_bavarian_holidays(y)

        for ev in history:
            start_dt = datetime.fromisoformat(ev["start"])
            start_date = start_dt.date()

            if start_date >= now:
                continue

            if start_date in holidays:
                continue

            restored.append({
                "title": ev["title"],
                "start": start_dt,
                "end": datetime.fromisoformat(ev["end"]),
                "location": ev.get("location", ""),
                "url": ev.get("url", ""),
                "description": ev.get("description", ""),
                "all_day": ev.get("all_day", False)
            })

    combined = restored + all_events + proxy_events

    unique = {}
    for ev in combined:
        key = (ev["title"].lower().strip(), ev["start"].isoformat())
        if key not in unique:
            unique[key] = ev

    final_events = list(unique.values())

    print(f"Gesamtanzahl Events (inkl. Vergangenheit & Proxy): {len(final_events)}")

    save_history(final_events)

    generate_ics(final_events)


if __name__ == "__main__":
    main()
