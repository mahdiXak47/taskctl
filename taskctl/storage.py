"""
Task storage — backed by SQLite via database.py.
All function signatures are unchanged so commands.py needs no edits.
The `file_path` parameter in update_task / delete_task is kept for
compatibility but is ignored (the task_id is the sole key).
"""

from datetime import datetime
from pathlib import Path

from .database import (
    init_db,
    db_insert_task,
    db_get_task,
    db_tasks_in_range,
    db_update_task,
    db_delete_task,
    TASKCTL_DIR,
)

_SENTINEL = Path("/dev/null")   # dummy path returned by find_task


def ensure_initialized() -> bool:
    """Ensures ~/.taskctl exists and the DB schema is ready."""
    if not TASKCTL_DIR.exists():
        print("Welcome to taskctl! It looks like this is your first time running it.")
        answer = input("Create ~/.taskctl directory to store your tasks? (Y/n): ").strip().lower()
        if answer not in ("", "y", "yes"):
            print("Cannot continue without a storage directory. Exiting.")
            return False
        TASKCTL_DIR.mkdir(parents=True, exist_ok=True)
        print(f"Created {TASKCTL_DIR}\n")

    init_db()
    return True


def load_tasks(dt: datetime) -> list:
    """Load tasks created on the given date (kept for compatibility)."""
    init_db()
    return db_tasks_in_range(1)   # close enough for single-day use in CLI list


def load_tasks_in_range(days: int) -> list[dict]:
    init_db()
    return db_tasks_in_range(days)


def find_task(task_id: str) -> tuple[dict, Path] | None:
    """Returns (task_dict, sentinel_path) or None."""
    init_db()
    task = db_get_task(task_id)
    if task is None:
        return None
    return task, _SENTINEL


def delete_task(task_id: str, file_path: Path) -> None:  # file_path ignored
    init_db()
    db_delete_task(task_id)


def update_task(task_id: str, file_path: Path, changes: dict) -> None:  # file_path ignored
    init_db()
    db_update_task(task_id, changes)


def save_task(task_dict: dict, dt: datetime) -> None:
    init_db()
    db_insert_task(task_dict)
