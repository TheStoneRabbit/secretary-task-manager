#!/usr/bin/env python3
"""
Automatic Task Archival System
Moves completed tasks older than 2 weeks from tasks.md to archived/completed.md
"""

import re
from datetime import datetime, timedelta
from pathlib import Path


class TaskArchiver:
    def __init__(self, tasks_file, archive_file):
        self.tasks_file = Path(tasks_file)
        self.archive_file = Path(archive_file)
        self.two_weeks_ago = datetime.now().date() - timedelta(days=14)

    def parse_completed_date(self, task_line):
        """Extract completion date from task line"""
        # Pattern: [Completed: MM/DD/YYYY] or [Completed: YYYY-MM-DD]
        patterns = [
            r"\[Completed: (\d{2}/\d{2}/\d{4})\]",  # MM/DD/YYYY
            r"\[Completed: (\d{4}-\d{2}-\d{2})\]",  # YYYY-MM-DD
        ]

        for pattern in patterns:
            match = re.search(pattern, task_line)
            if match:
                date_str = match.group(1)
                try:
                    if "/" in date_str:
                        return datetime.strptime(date_str, "%m/%d/%Y").date()
                    else:
                        return datetime.strptime(date_str, "%Y-%m-%d").date()
                except:
                    continue

        return None

    def should_archive(self, task_line):
        """Check if task should be archived (completed > 2 weeks ago)"""
        if not task_line.strip().startswith("- [x]"):
            return False

        completed_date = self.parse_completed_date(task_line)
        if not completed_date:
            return False

        return completed_date <= self.two_weeks_ago

    def archive_old_tasks(self):
        """Move old completed tasks to archive"""
        if not self.tasks_file.exists():
            print(f"❌ Tasks file not found: {self.tasks_file}")
            return

        # Read current tasks
        with open(self.tasks_file, "r") as f:
            lines = f.readlines()

        # Separate tasks to keep vs archive
        tasks_to_keep = []
        tasks_to_archive = []
        in_completed_section = False

        for line in lines:
            # Track if we're in the Completed section
            if line.startswith("## Completed"):
                in_completed_section = True
                tasks_to_keep.append(line)
                continue

            # If we hit another section header, we're out of completed
            if line.startswith("##") and in_completed_section:
                in_completed_section = False

            # Check if this completed task should be archived
            if in_completed_section and self.should_archive(line):
                tasks_to_archive.append(line)
            else:
                tasks_to_keep.append(line)

        if not tasks_to_archive:
            print("✅ No tasks to archive (none older than 2 weeks)")
            return

        # Write updated tasks.md
        with open(self.tasks_file, "w") as f:
            f.writelines(tasks_to_keep)

        # Append archived tasks to completed.md
        with open(self.archive_file, "r") as f:
            archive_content = f.read()

        with open(self.archive_file, "w") as f:
            f.write(archive_content)
            if not archive_content.endswith("\n"):
                f.write("\n")

            # Add archive timestamp
            f.write(f"\n### Archived on {datetime.now().strftime('%B %d, %Y')}\n\n")

            # Write archived tasks
            for task in tasks_to_archive:
                f.write(task)

            f.write("\n")

        print(f"📦 Archived {len(tasks_to_archive)} task(s) to {self.archive_file}")
        for task in tasks_to_archive:
            # Extract just the task title for display
            task_title = task.split("[")[0].replace("- [x]", "").strip()
            print(f"   ✓ {task_title[:80]}")

        return len(tasks_to_archive)

    def add_timestamp_to_completed(self, task_title):
        """Add timestamp to a newly completed task in tasks.md"""
        if not self.tasks_file.exists():
            return

        with open(self.tasks_file, "r") as f:
            content = f.read()

        # Find the task line and add timestamp if not present
        lines = content.split("\n")
        modified = False

        for i, line in enumerate(lines):
            if task_title in line and line.strip().startswith("- [x]"):
                # Check if it already has a timestamp
                if "[Completed:" not in line:
                    # Add timestamp
                    timestamp = datetime.now().strftime("%m/%d/%Y")
                    # Insert timestamp before the last bracket or at the end
                    lines[i] = line.rstrip() + f" [Completed: {timestamp}]"
                    modified = True
                    break

        if modified:
            with open(self.tasks_file, "w") as f:
                f.write("\n".join(lines))
            print(f"⏰ Added timestamp to completed task: {task_title[:60]}...")


def main():
    """Run the archival system"""
    base_dir = Path(__file__).parent.parent  # Task-Manager root
    tasks_file = base_dir / "tasks.md"
    archive_file = base_dir / "archived" / "completed.md"

    archiver = TaskArchiver(tasks_file, archive_file)
    archiver.archive_old_tasks()


if __name__ == "__main__":
    main()
