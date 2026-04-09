#!/usr/bin/env python3
"""
Configuration loader for Task Manager
Reads .env file to get repository location
"""

from pathlib import Path
import os


def load_env(env_file):
    """Load environment variables from .env file"""
    env_vars = {}
    if not env_file.exists():
        return env_vars

    with open(env_file, "r") as f:
        for line in f:
            line = line.strip()
            # Skip comments and empty lines
            if not line or line.startswith("#"):
                continue
            # Parse KEY=VALUE
            if "=" in line:
                key, value = line.split("=", 1)
                env_vars[key.strip()] = value.strip()

    return env_vars


def get_base_dir():
    """
    Get the Task Manager base directory.

    Priority:
    1. TASK_MANAGER_DIR from .env file
    2. Auto-detect from script location (fallback)
    """
    # Try to find .env file
    # Start from this script's location and search upward
    current = Path(__file__).resolve().parent

    # Search up to 3 levels for .env file
    for _ in range(3):
        env_file = current / ".env"
        if env_file.exists():
            env_vars = load_env(env_file)
            if "TASK_MANAGER_DIR" in env_vars:
                base_dir = Path(env_vars["TASK_MANAGER_DIR"])
                if base_dir.exists():
                    return base_dir

        # Move up one directory
        if current.parent == current:  # Reached root
            break
        current = current.parent

    # Fallback: auto-detect from script location
    # Assume scripts are in src/ subdirectory
    return Path(__file__).resolve().parent.parent


def get_computer_name():
    """Get computer name from .env or return 'unknown'"""
    current = Path(__file__).resolve().parent

    for _ in range(3):
        env_file = current / ".env"
        if env_file.exists():
            env_vars = load_env(env_file)
            return env_vars.get("COMPUTER_NAME", "unknown")

        if current.parent == current:
            break
        current = current.parent

    return "unknown"


if __name__ == "__main__":
    # Test the config loader
    base_dir = get_base_dir()
    computer_name = get_computer_name()

    print(f"Base directory: {base_dir}")
    print(f"Computer name: {computer_name}")
    print(f"Tasks file: {base_dir / 'tasks.md'}")
    print(f"Calendar file: {base_dir / 'calendar.md'}")
