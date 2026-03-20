import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from ics import Calendar, Event

print("Script gestartet")


# ---------------------------------------------------------
# DAUER SETZEN
# ---------------------------------------------------------
def set_default_duration(event):
    name = event.name.lower()

    # RCQ
    if "rcq" in name or "regional championship" in name or "qualifier" in name:
        event.duration = timedelta(hours=6)
        return

    # Friday Night Magic Modern
    if ("friday night" in name or "fnm" in name) and "modern" in name:
        event.duration = timedelta(hours=4)
        return

    # After Work Modern
    if "after" in name and "modern" in name:
        event.duration = timedelta(hours=3)
        return

    # Store Championship
    if "store championship" in name or "championship" in name:
        event.duration = timedelta(hours=5)
        return


# ---------------------------------------------------------
# FILTER: NUR RELEVANTE EVENTS (NICHT DD-SPEZIFISCH)
# ---------------------------------------------------------
def is_relevant_event(event):
    name = event.name.lower()

    # RCQ (alle Shops)
    if any(x in name for x in [
        "rcq",
        "regional championship",
        "qualifier",
        "wpn qualifier",
        "store qualifier",
        "championship qualifier"
    ]):
        return True

    # Store Championship (alle Shops)
    if "store championship" in name or "championship" in name:
        return True

    # Friday Night Modern (alle Shops)
    if (
        any(x in name for x in ["friday night", "fnm", "friday night magic"])
        and "modern" in name
    ):
        return True

    # After Work Modern (alle Shops – praktisch nur DD)
    if "after work modern" in name or "after-work modern" in name or "afterwork modern" in name:
        return True

    return False


# ---------------------------------------------------------
# BB-SPIELE
# ---------------------------------------------------------
def fetch_bbspiele_events():
    print("Hole Events von BB-Spiele...")

    url = "https://www.bb-spiele.de/events?categories=0196a9a7d19270a89170491be8392535&p=1"
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        resp = requests.get(url, headers=headers)
    except Exception as e:
        print("Fehler bei BB-Spiele:", e)
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    events = []

    cards = soup.select(".events-card")

    for card in cards:
        title_el = card.select_one(".netzp-events-title")
        if not title_el:
            continue
        title = title_el.get_text(strip=True)

        date_el = card.select_one(".icon-calendar + span")
        if not date_el:
            continue

        raw = date_el.get_text(strip=True)
        parts = raw.split(",")
        if len(parts) < 3:
            continue

        date_str = parts[1].strip()
        time_str = parts[2].strip().split("-")[0].strip()

        try:
            dt = datetime.strptime(f"{date_str} {time_str}", "%d.%m.%y %H:%M")
        except:
            continue

        loc_el = card.select_one(".icon-marker + b")
        location = loc_el.get_text(strip=True) if loc_el else "BB-Spiele"

        desc_el = card.select_one(".card-text.lead")
        description = desc_el.get_text(strip=True) if desc_el else "Event von BB-Spiele"

        e = Event()
        e.name = title
        e.begin = dt
        e.location = location
        e.description = description

        set_default_duration(e)
        events.append(e)

    print(f"BB-Spiele Events gefunden: {len(events)}")
    return events


# ---------------------------------------------------------
# FUNTANIMENT
# ---------------------------------------------------------
def fetch_funtainment_events():
    print("Hole Events von Funtainment...")

    url = "https://www.funtainment.de/b2c-shop/tickets?categories=0197f53c9a997cbe8574b9211c0c8eaf&p=1"
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        resp = requests.get(url, headers=headers)
    except Exception as e:
        print("Fehler bei Funtainment:", e)
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    events = []

    cards = soup.select(".events-card")

    for card in cards:
        title_el = card.select_one(".netzp-events-title")
        if not title_el:
            continue
        title = title_el.get_text(strip=True)

        date_el = card.select_one(".icon-calendar + span")
        if not date_el:
            continue

        raw = date_el.get_text(strip=True)
        parts = raw.split(",")
        if len(parts) < 3:
            continue

        date_str = parts[1].strip()
        time_str = parts[2].strip().split("-")[0].strip()

        try:
            dt = datetime.strptime(f"{date_str} {time_str}", "%d.%m.%y %H:%M")
        except:
            continue

        loc_el = card.select_one(".icon-marker + b")
        location = loc_el.get_text(strip=True) if loc_el else "Funtainment München"

        desc_el = card.select_one(".card-text.lead")
        description = desc_el.get_text(strip=True) if desc_el else "Event von Funtainment"

        e = Event()
        e.name = title
        e.begin = dt
        e.location = location
        e.description = description

        set_default_duration(e)
        events.append(e)

    print(f"Funtainment Events gefunden: {len(events)}")
    return events


# ---------------------------------------------------------
# DECK & DICE / DD MUNICH
# ---------------------------------------------------------
def fetch_ddmunich_events():
    print("Hole Events von Deck & Dice / DD Munich...")

    url = "https://www.dd-munich.de/event-list"
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        resp = requests.get(url, headers=headers)
    except Exception as e:
        print("Fehler bei DD Munich:", e)
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    events = []

    cells = soup.select("[data-hook^='calendar-cell-']")

    for cell in cells:
        data_hook = cell.get("data-hook")
        if not data_hook:
            continue

        try:
            iso = data_hook.replace("calendar-cell-", "")
            date = datetime.fromisoformat(iso.replace("Z", ""))
        except:
            continue

        items = cell.select(".x336W1")

        for item in items:
            title_el = item.select_one(".OyuNR8")
            if not title_el:
                continue

            title = title_el.get_text(strip=True)
            name_lower = title.lower()

            # Wir wollen hier NUR:
            # - Friday Night Modern 18.30
            # - After Work Modern - 19:00 Uhr
            if "friday night modern" in name_lower:
                hour, minute = 18, 30
            elif "after work modern" in name_lower or "after-work modern" in name_lower or "afterwork modern" in name_lower:
                hour, minute = 19, 0
            else:
                # alle anderen DD-Events ignorieren
                continue

            dt = datetime(
                year=date.year,
                month=date.month,
                day=date.day,
                hour=hour,
                minute=minute,
            )

            e = Event()
            e.name = title
            e.begin = dt
            e.location = "Deck & Dice / DD Munich"
            e.description = "Event von Deck & Dice / DD Munich"

            set_default_duration(e)
            events.append(e)

    print(f"DD Munich Events gefunden: {len(events)}")
    return events


# ---------------------------------------------------------
# GENERATE ICS
# ---------------------------------------------------------
def generate_ics():
    print("Erzeuge Kalender...")

    cal = Calendar()

    bb = fetch_bbspiele_events()
    ft = fetch_funtainment_events()
    dd = fetch_ddmunich_events()

    all_events = bb + ft + dd

    # Filter (DD ist durch fetch_ddmunich_events schon stark eingeschränkt)
    all_events = [e for e in all_events if is_relevant_event(e)]

    # Duplikate entfernen
    unique = {}
    for e in all_events:
        key = (e.name.lower(), e.begin)
        unique[key] = e
    all_events = list(unique.values())

    # Sortieren
    all_events.sort(key=lambda e: e.begin)

    print("Gesamtanzahl Events:", len(all_events))

    for e in all_events:
        cal.events.add(e)

    print("Schreibe magic.ics...")
    with open("magic.ics", "w", encoding="utf-8") as f:
        f.writelines(cal)

    print("Fertig! Datei erzeugt.")


if __name__ == "__main__":
    generate_ics()
