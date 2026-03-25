import json
import re
from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path
from telegram.ext import ApplicationBuilder, MessageHandler, filters

TZ = ZoneInfo("Europe/Berlin")
CUSTOM_EVENTS_FILE = Path("custom_events.json")

BOT_TOKEN = "8624373741:AAG_0-PNhM0ZvE90yQCtueVKip37aDYH2dE"


def save_event(event):
    if CUSTOM_EVENTS_FILE.exists():
        data = json.loads(CUSTOM_EVENTS_FILE.read_text(encoding="utf-8"))
    else:
        data = []

    data.append(event)
    CUSTOM_EVENTS_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")


def parse_event(text: str):
    """
    Erwartet Format wie:
    Modern bei Nils
    12.04.2026
    19:00-23:00
    Adresse: Musterstraße 12
    """

    lines = [l.strip() for l in text.split("\n") if l.strip()]
    if len(lines) < 3:
        return None

    title = lines[0]

    # Datum
    date_str = lines[1]
    date = datetime.strptime(date_str, "%d.%m.%Y").date()

    # Zeit
    time_match = re.search(r"(\d{1,2}:\d{2})\s*[-–]\s*(\d{1,2}:\d{2})", lines[2])
    if not time_match:
        return None

    start_time = datetime.strptime(time_match.group(1), "%H:%M").time()
    end_time = datetime.strptime(time_match.group(2), "%H:%M").time()

    start_dt = datetime.combine(date, start_time, tzinfo=TZ)
    end_dt = datetime.combine(date, end_time, tzinfo=TZ)

    # Ort (optional)
    location = ""
    for line in lines[3:]:
        if line.lower().startswith("adresse:"):
            location = line.split(":", 1)[1].strip()

    return {
        "title": f"Privat – {title}",
        "start": start_dt.isoformat(),
        "end": end_dt.isoformat(),
        "location": location,
        "url": "",
        "description": "Privates Event",
        "all_day": False
    }


async def handle_message(update, context):
    text = update.message.text

    event = parse_event(text)
    if not event:
        await update.message.reply_text(
            "Konnte das Event nicht verstehen.\n"
            "Format:\n"
            "Modern bei Nils\n"
            "12.04.2026\n"
            "19:00-23:00\n"
            "Adresse: Musterstraße 12"
        )
        return

    save_event(event)

    await update.message.reply_text(
        f"Event gespeichert:\n"
        f"{event['title']}\n"
        f"{event['start']} – {event['end']}\n"
        f"{event['location']}"
    )


def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()


if __name__ == "__main__":
    main()
