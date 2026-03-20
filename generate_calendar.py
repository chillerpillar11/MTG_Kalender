#!/usr/bin/env python3
import uuid
from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path

# Stores importieren
from stores.bb_spiele import fetch_bb_spiele_events
from stores.funtainment import fetch_funtainment_events
from stores.dd_munich import fetch_dd_munich_events

TZ = ZoneInfo("Europe/Berlin")


# ---------------------------------------------------------
# ICS-Helfer
# ---------------------------------------------------------
def format_dt(dt: datetime) -> str:
    """ICS-konforme Zeitformatierung."""
    return dt.astimezone(TZ).strftime("%Y%m%dT%H%M%S")


def generate_ics(events, filename="magic.ics"):
    """Erstellt eine ICS-Datei aus Event-Dictionaries."""
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Magic Munich Calendar//DE",
        "CALSCALE:GREGORIAN",
    ]

    for ev in events:
        uid = f"{uuid.uuid4()}@magic-munich"

        # --- VEVENT START ---
        lines.append("BEGIN:VEVENT")
        lines.append(f"UID:{uid}")
        lines.append(f"DTSTAMP:{format_dt(datetime.now(TZ))}")
        lines.append(f"DTSTART:{format_dt(ev['start'])}")
        lines.append(f"DTEND:{format_dt(ev['end'])}")
        lines.append(f"SUMMARY:{ev['title']}")
        lines.append(f"LOCATION:{ev.get('location', '')}")
        lines.append(f"URL:{ev.get('url', '')}")

        # Beschreibung OHNE Backslash im f-String
        desc = ev.get("description", "")
        desc = desc.replace("\n", " ").replace("\r", " ")
        lines.append(f"DESCRIPTION:{desc}")

        lines.append("END:VEVENT")
        # --- VEVENT END ---

    lines.append("END:VCALENDAR")

    Path(filename).write_text("\n".join(lines), encoding="utf-8")
    print(f"ICS erzeugt: {filename}")


# ---------------------------------------------------------
# FILTER
# ---------------------------------------------------------
def is_relevant_event(ev):
    name = ev["title"].lower()

    # Modern
    if "modern" in name:
        return True

    # RCQ / Qualifier
    if "rcq" in name or "regional championship" in name or "qualifier" in name:
        return True

    # Store Championship
    if "championship" in name:
        return True

    return False


# ---------------------------------------------------------
# MAIN
# ---------------------------------------------------------
def main():
    print("Script gestartet")
    print("Erzeuge Kalender...")

    all_events = []

    # BB-Spiele
    try:
        all_events.extend(fetch_bb_spiele_events())
    except Exception as e:
        print("Fehler bei BB-Spiele:", e)

    # Funtainment
    try:
        all_events.extend(fetch_funtainment_events())
    except Exception as e:
        print("Fehler bei Funtainment:", e)

    # Deck & Dice
    try:
        all_events.extend(fetch_dd_munich_events())
    except Exception as e:
        print("Fehler bei DD Munich:", e)

    print(f"Gesamtanzahl Events (ungefiltert): {len(all_events)}")

    # Filter anwenden
    filtered_events = [ev for ev in all_events if is_relevant_event(ev)]

    print(f"Gesamtanzahl Events (gefiltert): {len(filtered_events)}")

    generate_ics(filtered_events)


if __name__ == "__main__":
    main()

