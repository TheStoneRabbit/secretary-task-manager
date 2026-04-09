# Task Manager Template

A task management system powered by Claude Code with an intelligent skill agent, interactive HTML dashboard, and Outlook calendar sync.

## Features

- **Claude Code Skill** (`/work-tasks`) — AI-powered task management with rules for date checking, meeting alerts, overdue tracking, and dashboard sync
- **Interactive Dashboard** — HTML dashboard with timeline view, search, date filter, past events, completed tasks, and copy-to-clipboard
- **Outlook Calendar Sync** — Import meetings from ICS calendar feed into JSON, preserving manual annotations
- **Meeting Proximity Alerts** — Get warned when a meeting is within 30 minutes
- **Task JSON Format** — Structured task data with projects, priorities, contacts, subtasks, and metadata
- **Completed Event Tracking** — Past meetings automatically marked as completed with visual indicators
- **Automatic Archival** — Old completed tasks archived after 2 weeks

## Quick Setup

### 1. Clone and configure

```bash
git clone <this-repo>
cd Task-Manager-Template

# Copy and edit environment config
cp .env.example .env
# Edit .env with your repo path
```

### 2. Add your calendar (optional)

Create a `.calendar_sync_url` file with your Outlook ICS calendar URL:

```bash
echo "https://outlook.office365.com/owa/calendar/YOUR_URL/calendar.ics" > .calendar_sync_url
```

### 3. Sync and generate dashboard

```bash
bash refresh_calendar.sh
# Opens deadline_dashboard.html in your browser
```

### 4. Use the skill

In Claude Code, type `/work-tasks` to activate the skill. Then:

- "Add task: Review Q2 report, due Friday, high priority"
- "Show my dashboard"
- "What's on my calendar today?"
- "Mark the review task as done"
- "Plan my week"

## Directory Structure

```
.
├── .claude/skills/work-tasks/SKILL.md  # Claude Code skill definition
├── data/
│   ├── tasks.json                       # Task data (source of truth)
│   ├── calendar.json                    # Calendar data (source of truth)
│   └── README.md                        # Data format documentation
├── src/
│   ├── visualize_deadlines.py           # Dashboard generator
│   ├── import_ics_calendar.py           # ICS to JSON importer
│   ├── config.py                        # Path configuration
│   ├── archive_tasks.py                 # Task archival
│   ├── md_to_html.py                    # Markdown to HTML converter
│   └── session_start.py                 # Session initialization
├── notes/                               # Meeting notes (HTML for dashboard links)
├── emails/                              # Email drafts and references
├── current-work/                        # Work-in-progress documents
├── archived/                            # Archived completed tasks
├── refresh_calendar.sh                  # Calendar sync + dashboard refresh script
├── SKILL_CHANGELOG.md                   # Skill version history
└── deadline_dashboard.html              # Generated dashboard (open in browser)
```

## Customization

### Add your projects

Edit `.claude/skills/work-tasks/SKILL.md` and fill in the "Active Projects" section with your own projects, tech stacks, and task patterns. The skill uses this context to provide better suggestions.

### Dashboard theme

The dashboard uses a purple gradient theme by default. Edit `src/visualize_deadlines.py` to customize colors, layout, and styling.

### Calendar source

The system supports any ICS calendar feed (Outlook, Google Calendar, etc.). Just put the ICS URL in `.calendar_sync_url`.

## Requirements

- Python 3.10+
- `python-dateutil` (for recurring event support)
- Claude Code CLI

```bash
pip install python-dateutil
```

## How It Works

1. **Tasks** are stored in `data/tasks.json` — the skill reads and writes this file
2. **Calendar events** are imported from an ICS feed into `data/calendar.json`
3. **The dashboard** (`deadline_dashboard.html`) is generated from both JSON files
4. **The skill** enforces rules: always check the date, never move deadlines without asking, sync the dashboard after every change, alert on upcoming meetings

## License

MIT

## Credits

Built by Mason Lapine with Claude Code.
# secretary-task-manager
