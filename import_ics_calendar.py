#!/usr/bin/env python3
"""
Import meetings from Outlook ICS export to calendar.md
Parses .ics file and extracts upcoming meetings
"""

import json
import re
from datetime import datetime, timedelta
from pathlib import Path

from zoneinfo import ZoneInfo
from dateutil.rrule import rrulestr, rrule, WEEKLY, DAILY, MONTHLY, MO, TU, WE, TH, FR, SA, SU
from config import get_base_dir

# Microsoft Outlook timezone names -> IANA timezone names
MS_TZ_MAP = {
    "Eastern Standard Time": "America/New_York",
    "Central Standard Time": "America/Chicago",
    "Mountain Standard Time": "America/Denver",
    "Pacific Standard Time": "America/Los_Angeles",
    "UTC": "UTC",
    "GMT Standard Time": "Europe/London",
    "W. Europe Standard Time": "Europe/Berlin",
    "China Standard Time": "Asia/Shanghai",
    "Tokyo Standard Time": "Asia/Tokyo",
}

# Target timezone for display
LOCAL_TZ = ZoneInfo("America/New_York")


class ICSParser:
    def __init__(self, ics_file):
        self.ics_file = Path(ics_file)
        self.events = []
        self.today = datetime.now().date()

    def parse_ics(self):
        """Parse ICS file and extract events"""
        with open(self.ics_file, "r", encoding="utf-8") as f:
            content = f.read()

        # Split into individual events
        event_blocks = content.split("BEGIN:VEVENT")

        for block in event_blocks[1:]:  # Skip first empty block
            if "END:VEVENT" not in block:
                continue

            event = self.parse_event_block(block)
            if event:
                self.events.append(event)

        print(f"✅ Parsed {len(self.events)} total events from ICS")
        return self.events

    def parse_event_block(self, block):
        """Parse a single VEVENT block"""
        event = {}

        # Extract SUMMARY (title)
        summary_match = re.search(r"SUMMARY:(.+?)(?:\r?\n(?![^A-Z]))", block, re.DOTALL)
        if summary_match:
            summary = summary_match.group(1).replace("\r\n ", "").replace("\n ", "")
            event["summary"] = summary.strip()
        else:
            return None  # Skip events without summary

        # Skip canceled events
        if "Canceled:" in event["summary"] or "CANCELED" in event["summary"].upper():
            return None

        # Extract DTSTART (start time)
        dtstart_match = re.search(r"DTSTART(?:;TZID=([^:]+))?:(\d{8}T\d{6})(Z?)", block)
        if dtstart_match:
            tz_name = dtstart_match.group(1)
            dt_str = dtstart_match.group(2)
            is_utc = dtstart_match.group(3) == "Z"
            try:
                dt = datetime.strptime(dt_str, "%Y%m%dT%H%M%S")
                dt = self._convert_to_local(dt, tz_name, is_utc)
                event["start"] = dt
                event["date"] = dt.date()
            except:
                return None
        else:
            return None

        # Extract DTEND (end time)
        dtend_match = re.search(r"DTEND(?:;TZID=([^:]+))?:(\d{8}T\d{6})(Z?)", block)
        if dtend_match:
            tz_name = dtend_match.group(1)
            dt_str = dtend_match.group(2)
            is_utc = dtend_match.group(3) == "Z"
            try:
                dt = datetime.strptime(dt_str, "%Y%m%dT%H%M%S")
                dt = self._convert_to_local(dt, tz_name, is_utc)
                event["end"] = dt
            except:
                pass

        # Extract LOCATION
        location_match = re.search(
            r"LOCATION:(.+?)(?:\r?\n(?![^A-Z]))", block, re.DOTALL
        )
        if location_match:
            location = location_match.group(1).replace("\r\n ", "").replace("\n ", "")
            event["location"] = location.strip()

        # Extract DESCRIPTION
        desc_match = re.search(
            r"DESCRIPTION:(.+?)(?:\r?\n(?![^A-Z]))", block, re.DOTALL
        )
        if desc_match:
            desc = desc_match.group(1).replace("\r\n ", "").replace("\n ", "")
            event["description"] = desc.strip()

        # Check if it's a recurring event and capture RRULE
        rrule_match = re.search(r"RRULE:(.+?)(?:\r?\n)", block)
        if rrule_match:
            event["recurring"] = True
            event["rrule"] = rrule_match.group(1).strip()
        else:
            event["recurring"] = False

        # Check for RECURRENCE-ID (overrides for specific instances)
        recurrence_id_match = re.search(
            r"RECURRENCE-ID(?:;TZID=([^:]+))?:(\d{8}T\d{6})(Z?)", block
        )
        if recurrence_id_match:
            event["is_recurrence_override"] = True
            # Store the ORIGINAL date this override replaces
            tz_name = recurrence_id_match.group(1)
            rid_str = recurrence_id_match.group(2)
            is_utc = recurrence_id_match.group(3) == "Z"
            try:
                rid_dt = datetime.strptime(rid_str, "%Y%m%dT%H%M%S")
                rid_dt = self._convert_to_local(rid_dt, tz_name, is_utc)
                event["overrides_date"] = rid_dt.date()
            except:
                pass

        return event

    def _convert_to_local(self, dt, tz_name=None, is_utc=False):
        """Convert a datetime to local (America/New_York) time"""
        if is_utc:
            # UTC time, convert to local
            dt = dt.replace(tzinfo=ZoneInfo("UTC"))
            return dt.astimezone(LOCAL_TZ).replace(tzinfo=None)
        elif tz_name:
            # Look up the IANA timezone from Microsoft name
            iana_tz = MS_TZ_MAP.get(tz_name)
            if iana_tz:
                source_tz = ZoneInfo(iana_tz)
                dt = dt.replace(tzinfo=source_tz)
                local_dt = dt.astimezone(LOCAL_TZ)
                return local_dt.replace(tzinfo=None)
        # No timezone info or unknown timezone — assume already local
        return dt

    def _parse_rrule(self, rrule_str, dtstart):
        """Parse an RRULE string into a dateutil rrule object, handling timezone issues"""
        DAY_MAP = {"MO": MO, "TU": TU, "WE": WE, "TH": TH, "FR": FR, "SA": SA, "SU": SU}
        FREQ_MAP = {"WEEKLY": WEEKLY, "DAILY": DAILY, "MONTHLY": MONTHLY}

        parts = {}
        for part in rrule_str.split(";"):
            if "=" in part:
                key, val = part.split("=", 1)
                parts[key] = val

        freq = FREQ_MAP.get(parts.get("FREQ"))
        if not freq:
            return None

        kwargs = {"dtstart": dtstart, "freq": freq}

        if "INTERVAL" in parts:
            kwargs["interval"] = int(parts["INTERVAL"])

        if "UNTIL" in parts:
            until_str = parts["UNTIL"].rstrip("Z")
            try:
                kwargs["until"] = datetime.strptime(until_str, "%Y%m%dT%H%M%S")
            except:
                try:
                    kwargs["until"] = datetime.strptime(until_str, "%Y%m%d")
                except:
                    pass

        if "COUNT" in parts:
            kwargs["count"] = int(parts["COUNT"])

        if "BYDAY" in parts:
            days = []
            for d in parts["BYDAY"].split(","):
                d = d.strip()
                if d in DAY_MAP:
                    days.append(DAY_MAP[d])
            if days:
                kwargs["byweekday"] = days

        return rrule(**kwargs)

    def filter_upcoming_events(self, days_ahead=30, days_behind=365):
        """Filter events within range, expanding recurring events. Includes all past events for history."""
        upcoming = []
        cutoff_date = self.today + timedelta(days=days_ahead)
        lookback_date = self.today - timedelta(days=days_behind)

        # Collect recurrence overrides — track the ORIGINAL date being replaced
        override_dates = set()
        for event in self.events:
            if event.get("is_recurrence_override"):
                # Use the original date this override replaces, not the new date
                orig_date = event.get("overrides_date") or event.get("date")
                if orig_date:
                    override_dates.add((event.get("summary", "").strip(), orig_date))

        for event in self.events:
            event_date = event.get("date")
            if not event_date:
                continue

            # If this event has an RRULE, expand it
            if event.get("rrule") and not event.get("is_recurrence_override"):
                try:
                    dtstart = event["start"]
                    duration = (event["end"] - event["start"]) if event.get("end") else timedelta(hours=1)

                    # Parse RRULE manually to avoid timezone issues with rrulestr
                    rule = self._parse_rrule(event["rrule"], dtstart)
                    if rule:
                        for dt in rule:
                            d = dt.date()
                            if d > cutoff_date:
                                break
                            if d < lookback_date:
                                continue
                            # Skip if there's a specific override for this date
                            if (event.get("summary", "").strip(), d) in override_dates:
                                continue
                            # Create a copy for this occurrence
                            occurrence = dict(event)
                            occurrence["start"] = dt
                            occurrence["end"] = dt + duration
                            occurrence["date"] = d
                            upcoming.append(occurrence)
                    else:
                        # Couldn't parse RRULE, fall back
                        if lookback_date <= event_date <= cutoff_date:
                            upcoming.append(event)
                except Exception as e:
                    # If RRULE parsing fails, fall back to single event
                    if lookback_date <= event_date <= cutoff_date:
                        upcoming.append(event)
            else:
                # Non-recurring event or recurrence override
                if lookback_date <= event_date <= cutoff_date:
                    upcoming.append(event)

        # Deduplicate by (title, date, start_time)
        seen = set()
        deduped = []
        for event in upcoming:
            key = (event.get("summary", ""), event.get("date"), event.get("start"))
            if key not in seen:
                seen.add(key)
                deduped.append(event)

        # Sort by date and time
        deduped.sort(key=lambda x: x.get("start"))

        print(f"✅ Found {len(deduped)} upcoming events (next {days_ahead} days)")
        return deduped

    def format_for_calendar_json(self, events, existing_json_path=None):
        """Format events for data/calendar.json, preserving manual annotations"""
        # Load existing JSON to preserve manual fields (prep_notes, agenda_link, etc.)
        existing_events = {}
        if existing_json_path and Path(existing_json_path).exists():
            with open(existing_json_path, "r") as f:
                existing_data = json.load(f)
            for ev in existing_data.get("events", []):
                # Key by date + title for matching
                key = (ev.get("date", ""), ev.get("title", ""))
                existing_events[key] = ev

        json_events = []
        event_counter = 1

        for event in events:
            date_str = event["date"].strftime("%Y-%m-%d")
            start_time = event["start"].strftime("%I:%M %p").lstrip("0")
            end_time = event["end"].strftime("%I:%M %p").lstrip("0") if event.get("end") else start_time
            title = event["summary"]

            # Check for existing event to preserve manual annotations
            existing = existing_events.get((date_str, title), {})

            # Extract zoom link from location or description
            zoom_link = existing.get("zoom_link")
            location = existing.get("location")
            meeting_id = existing.get("meeting_id")
            dial_in = existing.get("dial_in")
            notes = existing.get("notes")

            raw_location = event.get("location", "")
            raw_desc = event.get("description", "")

            if not zoom_link:
                # Check location for zoom
                zoom_match = re.search(r"(https://[a-z]+\.zoom\.us/[^\s;]+)", raw_location)
                if zoom_match:
                    zoom_link = zoom_match.group(1)
                else:
                    # Check description
                    zoom_match = re.search(r"(https://[a-z]+\.zoom\.us/[^\s]+)", raw_desc)
                    if zoom_match:
                        zoom_link = zoom_match.group(1)

            if not location:
                # Extract physical location (not URLs)
                if raw_location:
                    parts = [p.strip() for p in raw_location.split(";")]
                    physical = [p for p in parts if not p.startswith("https://")]
                    if physical:
                        location = "; ".join(physical)

            if not meeting_id:
                mid_match = re.search(r"Meeting ID:\s*(\d[\d\s]+)", raw_desc)
                if mid_match:
                    meeting_id = mid_match.group(1).replace(" ", "")

            if not dial_in:
                phone_match = re.search(r"Telephone[：:]\s*([0-9\-]+)", raw_desc)
                if phone_match:
                    dial_in = phone_match.group(1)

            if not notes:
                # Extract short useful notes from description
                if raw_desc:
                    desc_lines = raw_desc.split("\\n")
                    for line in desc_lines[:5]:
                        line = line.strip()
                        if (line and not line.startswith("http") and len(line) < 100
                                and "safelinks" not in line.lower()
                                and "zoom.us" not in line.lower()
                                and "____" not in line):
                            if not any(skip in line.lower() for skip in
                                       ["invited to", "join from", "meeting id", "telephone"]):
                                notes = line
                                break

            json_event = {
                "id": existing.get("id", f"event-{event_counter:03d}"),
                "date": date_str,
                "start_time": start_time,
                "end_time": end_time,
                "title": title,
                "type": existing.get("type", "meeting"),
                "is_personal": existing.get("is_personal", False),
                "location": location,
                "zoom_link": zoom_link,
                "meeting_id": meeting_id,
                "dial_in": dial_in,
                "recurring": event.get("recurring", False),
                "notes": notes,
                "agenda_link": existing.get("agenda_link"),
                "prep_notes": existing.get("prep_notes"),
            }

            json_events.append(json_event)
            event_counter += 1

        return {
            "metadata": {
                "last_updated": datetime.now().strftime("%Y-%m-%d"),
                "version": "1.0"
            },
            "events": json_events
        }


def main():
    base_dir = get_base_dir()  # Get from .env or auto-detect
    ics_file = base_dir / "calendar.ics"
    calendar_json = base_dir / "data" / "calendar.json"

    if not ics_file.exists():
        print(f"❌ Error: {ics_file} not found")
        return

    print(f"📅 Parsing calendar from: {ics_file}")
    print("")

    parser = ICSParser(ics_file)
    parser.parse_ics()

    # Get upcoming events (next 30 days by default)
    upcoming = parser.filter_upcoming_events(days_ahead=30)

    if not upcoming:
        print("ℹ️ No upcoming events found in the next 30 days")
        return

    # Write data/calendar.json (preserving manual annotations)
    calendar_json_data = parser.format_for_calendar_json(upcoming, calendar_json)
    with open(calendar_json, "w") as f:
        json.dump(calendar_json_data, f, indent=2)
    print(f"✅ Calendar JSON updated: {calendar_json}")

    print("")
    print("📊 Summary:")
    print(f"   Total events imported: {len(upcoming)}")
    print(f"   Date range: {upcoming[0]['date']} to {upcoming[-1]['date']}")
    print("")
    print("💡 Next steps:")
    print("   1. Review data/calendar.json to verify meetings")
    print("   2. Add any manual annotations or task links")
    print("   3. Run: python3 src/visualize_deadlines.py")
    print("   4. Refresh your dashboard to see updated calendar")


if __name__ == "__main__":
    main()
