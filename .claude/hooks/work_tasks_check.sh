#!/bin/bash
# work-tasks pre-prompt check hook
# Runs on every UserPromptSubmit event when working in this project.
# Outputs current date/time and any meetings within 30 minutes,
# so the assistant cannot skip Rule 0 (date check) or Rule 0a (meeting alert).

# Resolve project root from this script's location
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/../.." && pwd )"

echo "=== work-tasks pre-prompt check ==="
date "+Current date/time: %A, %B %d, %Y - %I:%M %p"

CALENDAR_FILE="$PROJECT_ROOT/data/calendar.json"

if [ -f "$CALENDAR_FILE" ]; then
    python3 - "$CALENDAR_FILE" <<'PYEOF'
import json
import sys
from datetime import datetime, timedelta

calendar_path = sys.argv[1]

try:
    now = datetime.now()
    window = now + timedelta(minutes=30)
    today_str = now.strftime('%Y-%m-%d')

    with open(calendar_path) as f:
        data = json.load(f)

    alerts = []
    for e in data.get('events', []):
        if e.get('date') != today_str:
            continue
        if e.get('is_personal'):
            continue
        try:
            start = datetime.strptime(
                f"{e['date']} {e['start_time']}", '%Y-%m-%d %I:%M %p'
            )
            if now <= start <= window:
                mins = int((start - now).total_seconds() / 60)
                alerts.append(
                    f"⚠️  MEETING IN {mins} MIN: {e['start_time']} - {e['title']}"
                )
        except Exception:
            continue

    if alerts:
        print()
        print("--- UPCOMING MEETING ALERT ---")
        for a in alerts:
            print(a)
        print("Prepend a heads-up to your response per Rule 0a.")
        print("------------------------------")
except Exception:
    # Hook must never block the prompt; fail silent.
    pass
PYEOF
fi
