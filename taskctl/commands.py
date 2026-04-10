import uuid
from datetime import datetime, timedelta
from typing import Optional

from .models import (
    Task,
    TIMESTAMP_FORMAT,
    STATUS_NOT_STARTED,
    STATUS_IN_PROGRESS,
    STATUS_BREACHED_DEADLINE,
    STATUS_DONE_INTIME,
    STATUS_DONE_BUT_BREACHED,
)
from .storage import ensure_initialized, save_task, load_tasks_in_range, find_task, delete_task, update_task

_ETA_MIN = timedelta(minutes=5)
_ETA_MAX = timedelta(days=7)


def _parse_eta(eta: str) -> Optional[timedelta]:
    units = {"m": "minutes", "h": "hours", "d": "days"}
    if not eta:
        return None
    unit = eta[-1]
    if unit not in units or not eta[:-1].isdigit():
        return None
    delta = timedelta(**{units[unit]: int(eta[:-1])})
    if not (_ETA_MIN <= delta <= _ETA_MAX):
        return None
    return delta


def _prompt_title() -> str:
    while True:
        value = input("Title: ").strip()
        if value:
            return value
        print("  Title cannot be empty.")


def _prompt_description() -> str:
    return input("Description (enter to skip): ").strip()


def _prompt_eta() -> Optional[str]:
    while True:
        value = input("ETA (5m–7d, e.g. 30m, 2h, 1d — enter to skip): ").strip()
        if not value:
            return None
        delta = _parse_eta(value)
        if delta is not None:
            return value
        print("  Invalid value. Use a number + m/h/d in the range 5m to 7d (e.g. 30m, 4h, 3d).")


def _prompt_start_now() -> bool:
    answer = input("Start now? (Y/n): ").strip().lower()
    return answer in ("", "y", "yes")


def cmd_list(duration: Optional[str]) -> None:
    if not ensure_initialized():
        return

    days = 1  # default: today only
    if duration:
        delta = _parse_eta(duration)
        if delta is None:
            print(f"  Invalid duration '{duration}'. Use a number followed by m/h/d (e.g. 7d, 24h).")
            return
        days = max(1, round(delta.total_seconds() / 86400) or 1)

    tasks = load_tasks_in_range(days)

    if not tasks:
        print("No tasks found.")
        return

    col_id = max(len(t.get("task_id", "")) for t in tasks)
    col_title = max(len(t.get("title", "")) for t in tasks)

    print(f"{'ID':<{col_id}}  {'TITLE':<{col_title}}  STATUS")
    print("-" * (col_id + col_title + 12))
    for t in tasks:
        print(f"{t.get('task_id', ''):<{col_id}}  {t.get('title', ''):<{col_title}}  {t.get('status', '')}")


def cmd_create(title: Optional[str], description: Optional[str], eta: Optional[str], start: bool) -> None:
    if not ensure_initialized():
        return

    # Interactive prompts for any missing required/optional fields
    if title is None:
        title = _prompt_title()
    if description is None:
        description = _prompt_description()
    if eta is None:
        eta = _prompt_eta()
    if not start:
        start = _prompt_start_now()

    now = datetime.now()
    task_id = str(uuid.uuid4())[:8]
    delta = _parse_eta(eta) if eta else None

    started_time = now.strftime(TIMESTAMP_FORMAT) if start else None
    expected_end_time = (now + delta).strftime(TIMESTAMP_FORMAT) if (start and delta) else None

    task = Task(
        task_id=task_id,
        title=title,
        description=description,
        comments=[],
        eta=eta,
        created_time=now.strftime(TIMESTAMP_FORMAT),
        started_time=started_time,
        expected_end_time=expected_end_time,
        end_time=None,
        status=STATUS_IN_PROGRESS if start else STATUS_NOT_STARTED,
    )

    save_task(task.to_dict(), now)

    print(f"\nTask created [id: {task_id}]")
    print(f"  Title : {title}")
    print(f"  Status: {task.status}")
    if eta:
        print(f"  ETA   : {eta}")
    if expected_end_time:
        print(f"  Due by: {expected_end_time}")


def cmd_delete(task_id: str) -> None:
    if not ensure_initialized():
        return

    result = find_task(task_id)
    if result is None:
        print(f"No task found with id '{task_id}'.")
        return

    task, file_path = result

    if task.get("status") == STATUS_IN_PROGRESS:
        print(f"Task '{task.get('title')}' is currently in progress.")
        answer = input("Are you sure you want to delete it? (y/N): ").strip().lower()
        if answer not in ("y", "yes"):
            print("Deletion cancelled.")
            return

    delete_task(task_id, file_path)
    print(f"Task '{task_id}' deleted.")


def cmd_done(task_id: str) -> None:
    if not ensure_initialized():
        return

    result = find_task(task_id)
    if result is None:
        print(f"No task found with id '{task_id}'.")
        return

    task, file_path = result
    status = task.get("status")

    if status == STATUS_NOT_STARTED or task.get("started_time") is None:
        print("This task has not been started yet.")
        return

    if status not in (STATUS_IN_PROGRESS, STATUS_BREACHED_DEADLINE):
        print(f"Task is already '{status}' and cannot be marked done.")
        return

    now = datetime.now()
    new_status = STATUS_DONE_INTIME if status == STATUS_IN_PROGRESS else STATUS_DONE_BUT_BREACHED
    update_task(task_id, file_path, {
        "status": new_status,
        "end_time": now.strftime(TIMESTAMP_FORMAT),
    })

    if status == STATUS_IN_PROGRESS:
        print("Great, you have done the task in the estimated time!")
    else:
        print("Not bad, you done the task after all. Estimate better next time or work harder!")


def cmd_comment(task_id: str, message: str) -> None:
    if not ensure_initialized():
        return

    result = find_task(task_id)
    if result is None:
        print(f"No task found with id '{task_id}'.")
        return

    task, file_path = result
    comments = task.get("comments") or []
    comments.append({
        "text": message,
        "created_at": datetime.now().strftime(TIMESTAMP_FORMAT),
    })
    update_task(task_id, file_path, {"comments": comments})
    print(f"Comment added to task '{task_id}'.")
