from datetime import datetime, timedelta
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


def load_tasks_in_range(days: int) -> list[dict]:
    """Return all tasks from daily files covering the last `days` days."""
    now = datetime.now()
    tasks = []
    for offset in range(days):
        dt = now - timedelta(days=offset)
        tasks.extend(load_tasks(dt))
    return tasks


def find_task(task_id: str) -> tuple[dict, Path] | None:
    """Search all daily YAML files for a task by id. Returns (task_dict, file_path) or None."""
    for path in sorted(TASKCTL_DIR.glob("tasks-created-*.yaml")):
        with path.open("r") as f:
            tasks = yaml.safe_load(f) or []
        for task in tasks:
            if task.get("task_id") == task_id:
                return task, path
    return None


def delete_task(task_id: str, file_path: Path) -> None:
    with file_path.open("r") as f:
        tasks = yaml.safe_load(f) or []
    tasks = [t for t in tasks if t.get("task_id") != task_id]
    with file_path.open("w") as f:
        yaml.dump(tasks, f, default_flow_style=False, allow_unicode=True, sort_keys=False)


def save_task(task_dict: dict, dt: datetime) -> None:
    path = _daily_file(dt)
    tasks = load_tasks(dt)
    tasks.append(task_dict)
    with path.open("w") as f:
        yaml.dump(tasks, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
