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

        lines.append("BEGIN:VEVENT")
        lines.append(f"UID:{uid}")
        lines.append(f"DTSTAMP:{format_dt(datetime.now(TZ))}")
        lines.append(f"DTSTART:{format_dt(ev['start'])}")
        lines.append(f"DTEND:{format_dt(ev['end'])}")
        lines.append(f"SUMMARY:{ev['title']}")
        lines.append(f"LOCATION:{ev.get('location', '')}")
        lines.append(f"URL:{ev.get('url', '')}")

        # Backslash-freier DESCRIPTION-Block
        desc = ev.get("description", "").replace("\n", " ")
        lines.append(f"DESCRIPTION:{desc}")

        lines.append("END:VEVENT")

    lines.append("END:VCALENDAR")

    Path(filename).write_text("\n".join(lines), encoding="utf-8")
    print(f"ICS erzeugt: {filename}")


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

    print(f"Gesamtanzahl Events: {len(all_events)}")

    generate_ics(all_events)


if __name__ == "__main__":
    main()
