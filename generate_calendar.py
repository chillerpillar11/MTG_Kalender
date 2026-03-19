def fetch_wizards_events():
    events = []

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Accept": "application/json",
        "Referer": "https://locator.wizards.com/",
    }

    resp = requests.get(WIZARDS_URL, headers=headers)

    # Falls Wizards HTML statt JSON liefert → abbrechen
    if "text/html" in resp.headers.get("Content-Type", ""):
        print("Wizards API lieferte HTML statt JSON – wahrscheinlich Blockierung.")
        return events

    data = resp.json()

    for item in data.get("results", []):
        title = item.get("title")
        start = item.get("startDate")
        store = item.get("store", {}).get("name", "")
        address = item.get("store", {}).get("address", "")

        if not start:
            continue

        start_dt = datetime.fromisoformat(start.replace("Z", "+00:00"))

        e = Event()
        e.name = f"{title} – {store}"
        e.begin = start_dt
        e.location = address
        e.description = "WPN Event (RCQ oder Store Championship)"
        events.append(e)

    return events