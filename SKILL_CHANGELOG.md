# Skill Changelog

## Version 1.0.0 - Initial Release

**Features:**
- Task management with JSON format (data/tasks.json)
- Calendar sync from Outlook ICS (data/calendar.json)
- Interactive HTML dashboard with timeline view
- Search tasks and events (including past events)
- Date filter for browsing by date range
- Meeting proximity alerts (30-minute warning)
- Completed meeting/event badges
- Copy task button on all cards
- "Due This Week" counts through Sunday
- Overdue task management (never move dates without asking)
- HTML notes for dashboard links
- Automatic task archival (2+ weeks)
- Memory check on skill start (Rule -1)
- Calendar sync + dashboard refresh protocol
- Skill update protocol with changelog

**Rules:**
- Rule -1: Read memory on skill start
- Rule 0: Always check current date and time first
- Rule 0a: Meeting proximity alert (30 min)
- Rule 1: Never use hardcoded paths
- Rule 2: Calendar sync + dashboard refresh protocol
- Rule 2a: Overdue task management (never change dates without asking)
- Rule 2b: Notes linked to dashboard must be HTML
- Rule 3: Skill update protocol (always update changelog)
