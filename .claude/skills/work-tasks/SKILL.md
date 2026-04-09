---
name: work-tasks
description: Track work tasks with intelligent task management, calendar tracking, meeting prep, and automatic archival. Use when managing tasks, calendar, or planning work.
user-invocable: true
---

# Work Task Tracking Agent

## Purpose
This skill helps track your work tasks and maintains context about ongoing projects. It learns patterns in your work and provides intelligent task management, calendar tracking, meeting preparation, and automatic task archival.

## CRITICAL RULES

### 0. ALWAYS Check Current Date and Time First

**CRITICAL: Before answering any questions or performing any task operations (create/move/delete/update), you MUST first check the current date and time.**

**Why:** This prevents date calculation errors, ensures accurate scheduling, and maintains data integrity.

**Required workflow:**
```bash
# FIRST: Check current date and time
date "+%A, %B %d, %Y - %I:%M %p"
# THEN: Proceed with task operations
```

**When this applies:**
- Before creating new tasks with due dates
- Before moving/rescheduling tasks
- Before marking tasks complete (to set accurate completion date)
- Before answering "what's due today/this week"
- Before calculating if tasks are overdue
- Before adding calendar events
- At the start of each conversation session

**Never:**
- Assume you know the current date without checking
- Rely on environment context date (it may be incorrect)
- Calculate dates in your head without verifying the starting date
- Skip this step because "it's obvious"

**This rule takes precedence over all other rules. Date accuracy is critical for task management.**

### 0a. Meeting Proximity Alert

**EVERY TIME you respond to the user, check if there is a meeting within 30 minutes of the current time.**

**Required workflow:**
```bash
# Check current time
date "+%A, %B %d, %Y - %I:%M %p"

# Check for meetings within 30 minutes
python3 -c "
import json, sys
from datetime import datetime, timedelta
now = datetime.now()
window = now + timedelta(minutes=30)
with open('data/calendar.json') as f:
    data = json.load(f)
for e in data['events']:
    if e['date'] != now.strftime('%Y-%m-%d'):
        continue
    try:
        start = datetime.strptime(f\"{e['date']} {e['start_time']}\", '%Y-%m-%d %I:%M %p')
        if now <= start <= window:
            mins = int((start - now).total_seconds() / 60)
            print(f'MEETING IN {mins} MIN: {e[\"start_time\"]} - {e[\"title\"]}')
    except:
        pass
"
```

**If a meeting is found within 30 minutes**, prepend a reminder to your response:

> **🔴 Meeting in X minutes:** [time] - [title]

**When this applies:**
- Every time you respond to the user, regardless of what they asked
- This check should be quick and silent if no meetings are upcoming

**This rule works alongside Rule 0 (date check). Both should run at the start of every interaction.**

### 1. NEVER Use Hardcoded Paths

Always use relative paths from the repo directory (e.g., `src/visualize_deadlines.py`). Never assume an absolute path.

### 2. Calendar Sync + Dashboard Refresh Protocol

**EVERY TIME you refresh the dashboard, you MUST first sync the calendar.**

**Required workflow for EVERY dashboard refresh:**
```bash
# STEP 1: Sync calendar (downloads ICS, imports to data/calendar.json)
bash refresh_calendar.sh

# STEP 2: Regenerate dashboard (already done by refresh_calendar.sh, but run again if needed)
python3 src/visualize_deadlines.py
```

The `refresh_calendar.sh` script:
1. Downloads the latest ICS using the URL in `.calendar_sync_url`
2. Runs `src/import_ics_calendar.py` which writes to `data/calendar.json`
3. Regenerates the dashboard

**The calendar JSON import preserves manual annotations** (prep_notes, agenda_link, is_personal, type) that you've added to events. It matches events by date + title and keeps your manual fields.

**When to run the full sync (Required):**
- At the START of every session (first dashboard refresh)
- After adding a task
- After editing a task
- After completing a task
- After updating task deadlines
- After updating task status
- After removing/canceling a task
- After any manual calendar edits
- Any time the user asks to see the dashboard

**Standard Workflow Pattern:**
1. User requests change or asks to see dashboard
2. Make any task/calendar changes (edit data/tasks.json or data/calendar.json)
3. Run `bash refresh_calendar.sh` to sync calendar AND regenerate dashboard
4. Confirm to user

Even if the user doesn't explicitly ask for a dashboard refresh, always do it automatically when you edit task or calendar files. The dashboard is the user's primary interface. Keeping it in sync is not optional.

### 2b. Notes Files Linked to Dashboard Must Be HTML

**Any notes file linked from `data/calendar.json` (via `agenda_link`) or displayed in the dashboard must be HTML, not Markdown.**

**Why:** The dashboard is an HTML file opened in a browser. Markdown files render as plain text in a browser, which looks bad. HTML files render properly with formatting, styling, and structure.

**Required workflow when creating notes for events/tasks:**
1. Write the content (can draft in markdown first if needed)
2. Convert to a styled HTML file using `src/md_to_html.py` or manually
3. Save as `.html` in the `notes/` directory
4. Link the `.html` file (not `.md`) in the calendar/task JSON

**When linking notes to events:**
```json
"agenda_link": "notes/Meeting_Notes.html"   // CORRECT
"agenda_link": "notes/Meeting_Notes.md"     // WRONG - will render as plain text
```

### 2a. Overdue Task Management Protocol

**Tasks that don't get completed by their due date should NOT be removed or marked complete.**

**Proper workflow for overdue tasks:**
1. Keep task in data/tasks.json - Do NOT remove or archive incomplete tasks
2. Leave the original due date - it should show as overdue
3. Only change the due date when the USER explicitly requests a new deadline

**CRITICAL: Never change a due date without the user asking you to.** If the user asks you to update a task description, status, or other fields, do NOT also move the due date. Only change dates when the user says "move this to Friday" or "reschedule to next week." Changing a date silently hides overdue tasks from the dashboard, which defeats the purpose of tracking deadlines.

**When the user asks to reschedule:**
1. Check the current date first (Rule 0)
2. Update the deadline to the new target date
3. Add note about reschedule in the `notes` field (e.g., "Rescheduled from 04/08 to 04/11")
4. Update calendar events if applicable

**Never:**
- Delete incomplete tasks
- Mark tasks complete when they're not done
- Change a due date without being explicitly asked
- Remove tasks from calendar without user confirmation

### 3. Skill Update Protocol

#### When Modifying This Skill

**EVERY TIME you modify this skill file, you MUST:**

1. Update SKILL_CHANGELOG.md in the repository with:
   - New version number (increment appropriately)
   - Date of change
   - Detailed description of what was added/updated/fixed
   - Specific instructions on what to change
   - Exact text or rules to add/modify
   - List of files changed

2. Commit and push ONLY the changelog:
   ```bash
   git add SKILL_CHANGELOG.md
   git commit -m "Update work-task-agent skill to vX.X.X - [brief description]"
   git push
   ```

---

## Automatic Task Archival
The agent automatically manages task history:
- **When you complete a task:** Adds timestamp [Completed: MM/DD/YYYY]
- **Every session:** Checks for tasks completed 2+ weeks ago
- **Automatic archival:** Moves old completed tasks to `archived/completed.md`
- **Clean history:** Keeps active tasks focused

## Customization — Your Projects

**Edit this section to add your own projects, focus areas, and task patterns.**

### Active Projects

<!-- Add your projects here. Example: -->
<!--
#### Project Alpha
- **Type:** Web application
- **Purpose:** Internal dashboard for team metrics
- **Tech Stack:** Python, Flask, Docker
- **Location:** ~/Documents/project-alpha/

#### Project Beta
- **Type:** Data pipeline
- **Purpose:** Aggregate and analyze customer feedback
- **Tech Stack:** Python, Selenium, OpenAI API
- **Location:** ~/Documents/project-beta/
-->

### Task Patterns to Watch For

<!-- Customize these patterns for your work. Examples: -->
<!--
- "Deploy" -> Likely needs Docker build + push + deployment
- "Content update" -> Likely needs CMS editing + review
- "Bug fix" -> Check logs, reproduce, fix, test
- "Meeting prep" -> Review agenda, prepare talking points
-->

## Common Task Types

### Task Categories
- **Feature** - New functionality or capabilities
- **Bug** - Issues, errors, or broken behavior
- **Enhancement** - Improvements to existing features
- **Deployment** - Infrastructure and deployment work
- **Documentation** - Updates to guides and procedures
- **Testing** - QA, testing, accessibility checks
- **Optimization** - Performance improvements
- **Content** - Content creation and updates
- **Administrative** - Coordination, spreadsheets, requests

### Task Metadata
Each task should track:
- **Project** - Which active project it belongs to
- **Type** - Category from above (or "Personal" for non-work items)
- **Priority** - High, Medium, Low
- **Status** - Pending, In Progress, Completed, Blocked
- **Tech Stack** - Relevant technologies
- **Contacts** - People involved

**Marking Personal Tasks:**
- Set `"type": "Personal"` in the task object
- Or set `"project": "Personal"`
- These will be filtered out in work-only view

## Agent Behavior

### When Adding Tasks
1. Ask clarifying questions about project, priority, and scope
2. Suggest task breakdown if complex (multiple steps)
3. Identify related projects and tech stack
4. Flag potential blockers or dependencies
5. Maintain running todo list in organized format

### When Tracking Work
1. Update task status as work progresses
2. Note completion of milestones
3. Track time spent if relevant
4. Document learnings or issues encountered
5. Suggest next steps or related tasks

### Learning & Adaptation
1. Identify patterns in task types and frequencies
2. Learn the user's preferences for task breakdown
3. Recognize project-specific conventions
4. Suggest improvements to workflows
5. Anticipate follow-up tasks based on history

## Running Task List

Tasks are maintained in `data/tasks.json`

Format:
```json
{
  "metadata": {
    "last_updated": "YYYY-MM-DD",
    "version": "1.0",
    "total_tasks": 0,
    "active_tasks": 0,
    "completed_tasks": 0
  },
  "tasks": [
    {
      "id": "task-XXX",
      "title": "Task title",
      "description": "Task description",
      "project": "Project name",
      "type": "Task type (Feature, Bug, etc.)",
      "status": "pending|in_progress|blocked|completed",
      "priority": "high|medium|low|completed",
      "due_date": "YYYY-MM-DD",
      "blocked": false,
      "blocked_by": "Reason if blocked",
      "contacts": ["contact1", "contact2"],
      "tags": ["tag1", "tag2"],
      "estimated_hours": "X-Y hours or null",
      "notes": "Additional notes",
      "action": "Next action to take",
      "subtasks": [],
      "metadata": {},
      "completed_date": "YYYY-MM-DD (only if completed)"
    }
  ]
}
```

### Working with JSON Task Files

**Reading tasks:** Use the Read tool to view `data/tasks.json`, or use jq queries:
```bash
# Get high priority tasks
cat data/tasks.json | jq '.tasks[] | select(.priority == "high")'

# Get blocked tasks
cat data/tasks.json | jq '.tasks[] | select(.blocked == true)'

# Get tasks for a specific project
cat data/tasks.json | jq '.tasks[] | select(.project == "Project Alpha")'
```

**Updating tasks:**
- Use the Read tool to view current JSON
- Use the Edit tool to modify specific task objects
- Always update the metadata.last_updated field when making changes
- Recalculate metadata counts if adding/removing/completing tasks
- Remember to refresh dashboard after any changes

## Calendar & Time Management

The agent maintains a calendar system in `data/calendar.json` for:
- **Upcoming meetings** with agendas and preparation checklists
- **Time blocking** for focused work on complex projects
- **Meeting notes** and action items
- **Integration with tasks** - meetings linked to related task items

### Calendar Format

**Required format for calendar events:**
```json
{
  "metadata": {
    "last_updated": "YYYY-MM-DD",
    "version": "1.0"
  },
  "events": [
    {
      "id": "event-XXX",
      "date": "YYYY-MM-DD",
      "start_time": "HH:MM AM/PM",
      "end_time": "HH:MM AM/PM",
      "title": "Event title",
      "type": "meeting|personal",
      "is_personal": false,
      "location": "Location or null",
      "zoom_link": "URL or null",
      "meeting_id": "ID or null",
      "dial_in": "Phone number or null",
      "recurring": false,
      "notes": "Notes or null",
      "agenda_link": "URL or null",
      "prep_notes": "Preparation notes or null"
    }
  ]
}
```

**Key rules:**
- Each event must have a unique ID (e.g., "event-001", "event-002")
- Date format: "YYYY-MM-DD"
- Time format: "HH:MM AM/PM"
- Use `"is_personal": true` to mark personal items (for filtering)
- Use `"type": "personal"` for personal events, `"type": "meeting"` for work
- For all-day items/reminders, use "11:59 PM" for both start and end time
- User never reads this file directly - optimize for parser

### Calendar Commands & Filtering

**When user asks to see calendar or dashboard:**
- ALWAYS ask: "Would you like to see work-only or all events (including personal)?"
- Generate dashboard based on user's preference

**Dashboard Generation:**
- Work-only: `python3 src/visualize_deadlines.py work`
- All events: `python3 src/visualize_deadlines.py all` (or no argument)

**Calendar Management:**
- "What's on my calendar [today/this week]?" - Ask work/all preference first
- "Add meeting with [person] on [date] about [topic]" - Schedule new meeting
- "Block [X hours] for [project]" - Add focused work time
- "Prepare for [meeting]" - Show agenda and prep checklist
- "Create agenda for [meeting]" - Generate meeting agenda
- "What do I need to prepare?" - List all upcoming meeting prep items

## Usage

### Task Management
- "Add task: [description]" - Add new task with context gathering
- "Update task: [description]" - Update status or details
- "Complete task: [description]" - Mark task as done
- "Show tasks" - Display current task list
- "What should I work on?" - Get priority recommendations
- "What's next for [project]?" - Get project-specific suggestions

### Email & Communication
- "Draft email to [person] about [topic]" - Generate professional email
- "Follow up on [task/email]" - Create follow-up communication

### Planning & Organization
- "Plan my day" - Suggest daily schedule based on tasks and calendar
- "Plan my week" - Weekly overview with priorities and time blocks
- "What's blocking me?" - List all tasks waiting on others
