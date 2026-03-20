#!/usr/bin/env python3
import uuid
import json
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from pathlib import Path

# Stores importieren
from stores.bb_spiele import fetch_bb_spiele_events
from stores.funtainment import fetch_funtainment_events
from stores.dd_munich import fetch_dd_munich_events

TZ = ZoneInfo("Europe/Berlin")
HISTORY_FILE = Path("events_history.json")

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
    ]

    for ev in events:
        uid = f"{uuid.uuid4()}@magic-munich"

        lines.append("BEGIN:VEVENT")
        lines.append(f"UID:{uid}")
        lines.append(f"DTSTAMP:{format_dt(datetime.now(TZ))}")
        lines.append(f"DTSTART:{format_dt(ev['start'])}")
        lines.append(f"DTEND:{format_dt(ev['end'])}")
        lines.append(f"SUMMARY:{ev['title']}")
        lines.append(f"LOCATION:{ev.get('location', '')}")
        lines.append(f"URL:{ev.get('url', '')}")

        desc = ev.get("description", "")
        desc = desc.replace("\n", " ").replace("\r", " ")
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
    serializable = []
    for ev in events:
        serializable.append({
            "title": ev["title"],
            "start": ev["start"].isoformat(),
            "end": ev["end"].isoformat(),
            "location": ev.get("location", ""),
            "url": ev.get("url", ""),
            "description": ev.get("description", "")
        })
    HISTORY_FILE.write_text(json.dumps(serializable, indent=2), encoding="utf-8")


# ---------------------------------------------------------
# Proxy-Event-Generator (12 Wochen)
# ---------------------------------------------------------
def generate_proxy_events(event):
    title = event["title"].lower()

    # Wöchentliche Formate
    weekly_keywords = [
        "after work modern",
        "after work legacy",
        "after work premodern",
        "premodern",
        "legacy",
        "modern",  # Modern außer Friday Night Modern
    ]

    # 14-tägiges Format: Friday Night Modern
    fnm_modern_keywords = [
        "friday night modern",
        "friday night magic – modern",
        "friday night magic - modern",
        "friday night magic modern",
    ]

    # Prüfen, ob Friday Night Modern → 14 Tage
    is_fnm_modern = any(k in title for k in fnm_modern_keywords)

    # Prüfen, ob wöchentliches Format
    is_weekly = any(k in title for k in weekly_keywords)

    if not (is_fnm_modern or is_weekly):
        return []

    proxy_events = []
    start = event["start"]
    end = event["end"]

    for i in range(1, 13):  # 12 Wiederholungen
        if is_fnm_modern:
            delta = timedelta(weeks=2)
        else:
            delta = timedelta(weeks=1)

        new_start = start + delta * i
        new_end = end + delta * i

        proxy_events.append({
            "title": event["title"],
            "start": new_start,
            "end": new_end,
            "location": event.get("location", ""),
            "url": event.get("url", ""),
            "description": event.get("description", "")
        })

    return proxy_events


# ---------------------------------------------------------
# MAIN
# ---------------------------------------------------------
def main():
    print("Script gestartet")
    print("Erzeuge Kalender...")

    all_events = []

    # BB-Spiele
    try:
        events = fetch_bb_spiele_events()
        for ev in events:
            ev["title"] = f"BB-Spiele – {ev['title']}"
        all_events.extend(events)
    except Exception as e:
        print("Fehler bei BB-Spiele:", e)

    # Funtainment
    try:
        events = fetch_funtainment_events()
        for ev in events:
            ev["title"] = f"Funtainment – {ev['title']}"
        all_events.extend(events)
    except Exception as e:
        print("Fehler bei Funtainment:", e)

    # Deck & Dice
    try:
        events = fetch_dd_munich_events()
        for ev in events:
            ev["title"] = f"Deck & Dice – {ev['title']}"
        all_events.extend(events)
    except Exception as e:
        print("Fehler bei DD Munich:", e)

    print(f"Neue Events geladen: {len(all_events)}")

    # ---------------------------------------------------------
    # Proxy-Events erzeugen
    # ---------------------------------------------------------
    proxy_events = []
    for ev in all_events:
        proxy_events.extend(generate_proxy_events(ev))

    print(f"Erzeugte Proxy-Events: {len(proxy_events)}")

    # ---------------------------------------------------------
    # Alte Events laden
    # ---------------------------------------------------------
    history = load_history()

    restored = []
    for ev in history:
        restored.append({
            "title": ev["title"],
            "start": datetime.fromisoformat(ev["start"]),
            "end": datetime.fromisoformat(ev["end"]),
            "location": ev.get("location", ""),
            "url": ev.get("url", ""),
            "description": ev.get("description", "")
        })

    # ---------------------------------------------------------
    # Neue + Proxy + alte Events zusammenführen
    # ---------------------------------------------------------
    combined = restored + all_events + proxy_events

    # ---------------------------------------------------------
    # Duplikate entfernen (echte Events überschreiben Proxy)
    # ---------------------------------------------------------
    unique = {}
    for ev in combined:
        key = (ev["title"].lower().strip(), ev["start"].isoformat())
        unique[key] = ev  # echte Events überschreiben Proxy

    final_events = list(unique.values())

    print(f"Gesamtanzahl Events (inkl. Vergangenheit & Proxy): {len(final_events)}")

    # ---------------------------------------------------------
    # History aktualisieren
    # ---------------------------------------------------------
    save_history(final_events)

    # ---------------------------------------------------------
    # ICS erzeugen
    # ---------------------------------------------------------
    generate_ics(final_events)


if __name__ == "__main__":
    main()
