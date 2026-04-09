# Task Manager Data Files

This directory contains the **source of truth** for all tasks and calendar events in JSON format.

## Files

### `tasks.json`
Contains all active and completed tasks with full metadata.

**Structure:**
```json
{
  "metadata": {
    "last_updated": "2026-04-07",
    "version": "1.0",
    "total_tasks": 32,
    "active_tasks": 27,
    "completed_tasks": 5
  },
  "tasks": [
    {
      "id": "task-001",
      "title": "Task title",
      "description": "Full description",
      "project": "Project name",
      "type": "Certificate|Documentation|Development|etc",
      "status": "pending|blocked|completed",
      "priority": "high|medium|low",
      "due_date": "2026-04-07",
      "blocked": true/false,
      "blocked_by": "Person or reason",
      "contacts": ["Name 1", "Name 2"],
      "tags": ["tag1", "tag2"],
      "estimated_hours": "1-2 hours",
      "notes": "Additional context",
      "action": "Next action to take",
      "subtasks": [...],
      "metadata": {...},
      "completed_date": "2026-04-07"
    }
  ]
}
```

### `calendar.json`
Contains all calendar events and meetings.

**Structure:**
```json
{
  "metadata": {
    "last_updated": "2026-04-07",
    "version": "1.0"
  },
  "events": [
    {
      "id": "event-001",
      "date": "2026-04-07",
      "start_time": "12:30 PM",
      "end_time": "1:30 PM",
      "title": "Meeting title",
      "type": "meeting|personal",
      "is_personal": false,
      "location": "Room number or location",
      "zoom_link": "https://...",
      "meeting_id": "Meeting ID",
      "dial_in": "Phone number",
      "recurring": true/false,
      "notes": "Meeting notes",
      "agenda_link": "Link to agenda document"
    }
  ]
}
```

## Usage

### For AI Agents (OpenCode/Claude)
These JSON files are the **primary data source**. When updating tasks:
1. Edit `tasks.json` or `calendar.json` directly
2. Regenerate dashboard: `python3 src/visualize_deadlines.py work`

### For Humans
You don't need to edit these files manually. Just:
1. Tell OpenCode what you need: "Add a task to review the playbook, due May 8th"
2. OpenCode updates the JSON
3. View the dashboard in your browser

## Benefits of JSON

✅ **No text parsing** - Instant updates, no regex errors  
✅ **Structured data** - Every field has a defined type  
✅ **Easy queries** - "Show me all blocked tasks for Project Alpha"  
✅ **Version control friendly** - Clear diffs in git  
✅ **Extensible** - Easy to add new fields  
✅ **Tool integration** - Can export to any format  

## Migration

The original `tasks.md` and `calendar.md` files are still in the repository for reference, but they are **no longer the source of truth**. All updates go to JSON files.

If you need to view tasks in markdown format, you can always ask OpenCode to generate a markdown summary from the JSON data.
