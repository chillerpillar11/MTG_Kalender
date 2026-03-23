def generate_ics(events, filename="magic.ics"):
    """Erstellt eine ICS-Datei aus Event-Dictionaries."""
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Magic Munich Calendar//DE",
        "CALSCALE:GREGORIAN",

        # iPhone-Kalendername Fix
        "X-WR-CALNAME:Minga Boys Magic Kalender",
        "X-WR-TIMEZONE:Europe/Berlin",
    ]

    for ev in events:
        uid = f"{uuid.uuid4()}@magic-munich"

        lines.append("BEGIN:VEVENT")
        lines.append(f"UID:{uid}")
        lines.append(f"DTSTAMP:{format_dt(datetime.now(TZ))}")

        # ⭐ All-Day Events korrekt schreiben
        if ev.get("all_day"):
            # Enddatum ist EXKLUSIV → ICS-Standard
            lines.append(f"DTSTART;VALUE=DATE:{ev['start'].strftime('%Y%m%d')}")
            lines.append(f"DTEND;VALUE=DATE:{ev['end'].strftime('%Y%m%d')}")
        else:
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
