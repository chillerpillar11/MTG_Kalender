import pytz
from ics import Calendar, Event
from datetime import datetime
from bb_spiele import fetch_bb_spiele_events
from funtainment import fetch_funtainment_events
from dd_munich import fetch_dd_munich_events

TZ = pytz.timezone("Europe/Berlin")

def tag_store(events, store_name):
    """Fügt dem Titel einen Store‑Tag hinzu."""
    tagged = []
    for ev in events:
        ev["title"] = f"{store_name} {ev['title']}"
        ev["store"] = store_name  # optional, falls später benötigt
        tagged.append(ev)
    return tagged

def generate_calendar():
    print("Erzeuge Kalender...")

    all_events = []

    # --- BB-Spiele ---
    print("Hole Events von BB-Spiele...")
    bb_events = fetch_bb_spiele_events()
    bb_events = tag_store(bb_events, "BB-Spiele –")
    print(f"BB-Spiele Modern/RCQ Events gefunden: {len(bb_events)}")
    all_events.extend(bb_events)

    # --- Funtainment ---
    print("Hole Events von Funtainment...")
    ft_events = fetch_funtainment_events()
    ft_events = tag_store(ft_events, "Funtainment –")
    print(f"Funtainment Modern/RCQ Events gefunden: {len(ft_events)}")
    all_events.extend(ft_events)

    # --- Deck & Dice ---
    print("Hole Events von Deck & Dice / DD Munich...")
    dd_events = fetch_dd_munich_events()
    dd_events = tag_store(dd_events, "Deck & Dice –")
    print(f"Deck & Dice Modern/RCQ Events gefunden: {len(dd_events)}")
    all_events.extend(dd_events)

    # --- Duplikate entfernen ---
    print("\nEntferne Duplikate...")

    seen = set()
    unique_events = []

    for ev in all_events:
        # Der Schlüssel ist jetzt eindeutig, weil der Store im Titel steckt
        key = (ev["title"].lower().strip(), ev["start"])

        if key not in seen:
            seen.add(key)
            unique_events.append(ev)

    print(f"Gesamtanzahl Events: {len(unique_events)}")

    # --- ICS erzeugen ---
    cal = Calendar()

    for ev in unique_events:
        ics_event = Event()
        ics_event.name = ev["title"]
        ics_event.begin = ev["start"].astimezone(TZ)
        ics_event.end = ev["end"].astimezone(TZ)
        ics_event.location = ev.get("location", "")
        ics_event.description = ev.get("description", "")
        cal.events.add(ics_event)

    with open("magic.ics", "w", encoding="utf-8") as f:
        f.writelines(cal)

    print("ICS erzeugt: magic.ics")

if __name__ == "__main__":
    print("Script gestartet")
    generate_calendar()
