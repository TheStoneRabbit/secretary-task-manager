#!/usr/bin/env python3
"""
Session Start Check
Runs automatically when starting a work session with Claude
- Checks for tasks to archive (completed > 2 weeks ago)
- Quick, silent check that keeps tasks.md clean
"""

import sys
from pathlib import Path

# Import the archiver
sys.path.insert(0, str(Path(__file__).parent))
from archive_tasks import TaskArchiver


def quick_check():
    """Quick check and archive - runs silently unless there's something to report"""
    base_dir = Path(__file__).parent.parent  # Task-Manager root
    tasks_file = base_dir / "tasks.md"
    archive_file = base_dir / "archived" / "completed.md"

    archiver = TaskArchiver(tasks_file, archive_file)
    archived_count = archiver.archive_old_tasks()

    # Only return info if something was archived
    if archived_count and archived_count > 0:
        return f"🗄️ Archived {archived_count} old completed task(s)"

    return None


if __name__ == "__main__":
    result = quick_check()
    if result:
        print(result)
