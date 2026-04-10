import os
from datetime import datetime
from pathlib import Path

import yaml

TASKCTL_DIR = Path.home() / ".taskctl"


def ensure_initialized() -> bool:
    """Returns True if ~/.taskctl exists, prompts to create it if not."""
    if TASKCTL_DIR.exists():
        return True

    print("Welcome to taskctl! It looks like this is your first time running it.")
    answer = input("Create ~/.taskctl directory to store your tasks? (Y/n): ").strip().lower()
    if answer in ("", "y", "yes"):
        TASKCTL_DIR.mkdir(parents=True)
        print(f"Created {TASKCTL_DIR}\n")
        return True

    print("Cannot continue without a storage directory. Exiting.")
    return False


def _daily_file(dt: datetime) -> Path:
    date_str = dt.strftime("%d%B%Y").lower()  # e.g. 10april2026
    return TASKCTL_DIR / f"tasks-created-{date_str}.yaml"


def load_tasks(dt: datetime) -> list:
    path = _daily_file(dt)
    if not path.exists():
        return []
    with path.open("r") as f:
        data = yaml.safe_load(f) or []
    return data


def save_task(task_dict: dict, dt: datetime) -> None:
    path = _daily_file(dt)
    tasks = load_tasks(dt)
    tasks.append(task_dict)
    with path.open("w") as f:
        yaml.dump(tasks, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
