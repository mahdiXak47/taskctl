import uuid
from datetime import datetime, timedelta, date as date_type
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
from .storage import ensure_initialized, save_task, load_tasks_in_range, find_task, delete_task, update_task, record_event, get_task_last_event


def _format_timestamp(ts: str) -> str:
    """Return a human-friendly label for a stored timestamp string."""
    try:
        dt = datetime.strptime(ts, TIMESTAMP_FORMAT)
    except (ValueError, TypeError):
        return ts or ""

    now = datetime.now()
    diff = now - dt
    total_seconds = diff.total_seconds()
    time_str = dt.strftime("%H:%M")

    # Past timestamps
    if 0 <= total_seconds < 60 * 60:                   # 0-59 minutes ago
        minutes = max(1, int(total_seconds // 60))
        unit = "minute" if minutes == 1 else "minutes"
        return f"{minutes} {unit} ago"

    if total_seconds < 12 * 60 * 60:                   # 1-12 hours ago
        hours = int(total_seconds // 3600)
        unit = "hour" if hours == 1 else "hours"
        return f"{hours} {unit} ago"

    today = now.date()
    yesterday = today - timedelta(days=1)
    dt_date = dt.date()

    tomorrow = today + timedelta(days=1)

    if dt_date == today:
        return f"today {time_str}"
    if dt_date == yesterday:
        return f"yesterday {time_str}"
    if dt_date == tomorrow:
        return f"tomorrow {time_str}"

    return ts                                           # original for anything older/farther


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


def _last_event(task: dict) -> tuple[str, str]:
    """Return (event_type, timestamp) for the most recent event from the DB."""
    row = get_task_last_event(task["task_id"])
    if row:
        return (row["event_type"], row["timestamp"])
    return ("", "")


def cmd_list(duration: Optional[str], verbose: bool = False, status: Optional[str] = None) -> None:
    if not ensure_initialized():
        return

    _valid = (STATUS_NOT_STARTED, STATUS_IN_PROGRESS, STATUS_BREACHED_DEADLINE, STATUS_DONE_INTIME, STATUS_DONE_BUT_BREACHED)
    if status and status not in _valid:
        print(f"  Unknown status '{status}'.")
        print(f"  Valid values: {', '.join(_valid)}")
        return

    days = 1  # default: today only
    if duration:
        delta = _parse_eta(duration)
        if delta is None:
            print(f"  Invalid duration '{duration}'. Use a number followed by m/h/d (e.g. 7d, 24h).")
            return
        days = max(1, round(delta.total_seconds() / 86400) or 1)

    tasks = load_tasks_in_range(days)

    if status:
        tasks = [t for t in tasks if t.get("status") == status]

    if not tasks:
        print("No tasks found.")
        return

    col_id    = max(len(t.get("task_id", "")) for t in tasks)
    col_title = max(len(t.get("title",   "")) for t in tasks)

    if verbose:
        events = [_last_event(t) for t in tasks]
        col_event = max(
            len(f"{label} {_format_timestamp(ts)}" if label else "")
            for label, ts in events
        )
        col_event = max(col_event, len("EVENT"))
        print(f"{'ID':<{col_id}}  {'TITLE':<{col_title}}  {'STATUS':<20}  {'EVENT':<{col_event}}")
        print("-" * (col_id + col_title + col_event + 26))
        for t, (label, ts) in zip(tasks, events):
            event_str = f"{label} {_format_timestamp(ts)}" if label else ""
            print(
                f"{t.get('task_id',''):<{col_id}}  "
                f"{t.get('title',''):<{col_title}}  "
                f"{t.get('status',''):<20}  "
                f"{event_str:<{col_event}}"
            )
    else:
        print(f"{'ID':<{col_id}}  {'TITLE':<{col_title}}  STATUS")
        print("-" * (col_id + col_title + 12))
        for t in tasks:
            print(f"{t.get('task_id',''):<{col_id}}  {t.get('title',''):<{col_title}}  {t.get('status','')}")


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
    record_event(None, task_id, "created", now.strftime(TIMESTAMP_FORMAT))
    if start:
        record_event(None, task_id, "started", now.strftime(TIMESTAMP_FORMAT))

    print(f"\nTask created [id: {task_id}]")
    print(f"  Title : {title}")
    print(f"  Status: {task.status}")
    if eta:
        print(f"  ETA   : {eta}")
    if expected_end_time:
        print(f"  Due by: {_format_timestamp(expected_end_time)}")


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

    now = datetime.now()
    record_event(None, task_id, "deleted", now.strftime(TIMESTAMP_FORMAT))
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
    record_event(None, task_id, "is done", now.strftime(TIMESTAMP_FORMAT))

    if status == STATUS_IN_PROGRESS:
        print("Great, you have done the task in the estimated time!")
    else:
        print("Not bad, you done the task after all. Estimate better next time or work harder!")


def _format_remaining(expected_end_time: str) -> str:
    try:
        due = datetime.strptime(expected_end_time, TIMESTAMP_FORMAT)
    except (ValueError, TypeError):
        return "no deadline set"
    diff = due - datetime.now()
    if diff.total_seconds() < 0:
        secs = int(-diff.total_seconds())
        d, rem = divmod(secs, 86400)
        h, rem = divmod(rem, 3600)
        m = rem // 60
        parts = []
        if d: parts.append(f"{d}d")
        if h: parts.append(f"{h}h")
        if m: parts.append(f"{m}m")
        return f"deadline breached by {' '.join(parts) or '< 1m'}"
    secs = int(diff.total_seconds())
    d, rem = divmod(secs, 86400)
    h, rem = divmod(rem, 3600)
    m = rem // 60
    parts = []
    if d: parts.append(f"{d}d")
    if h: parts.append(f"{h}h")
    if m: parts.append(f"{m}m")
    return ' '.join(parts) or '< 1m'


def cmd_describe(task_id: str, verbose: bool = False) -> None:
    if not ensure_initialized():
        return

    result = find_task(task_id)
    if result is None:
        print(f"what task do you mean?")
        print(f"i do not find any task with id {task_id}")
        return

    task, _ = result
    title = task.get("title", "")
    status = task.get("status", "")
    expected_end_time = task.get("expected_end_time")
    comments = task.get("comments") or []

    print(f"{title} [{status}]")

    if expected_end_time:
        print(f"Time remaining: {_format_remaining(expected_end_time)}")
    else:
        print("Time remaining: no deadline set")

    if comments:
        print()
        displayed = comments if verbose else comments[-5:]
        if not verbose and len(comments) > 5:
            print(f"  (showing last 5 of {len(comments)} comments, use -v to see all)")
        for c in displayed:
            text = c.get("text", "")
            ts = c.get("created_at", "")
            print(f"  [{_format_timestamp(ts)}] {text}")
    else:
        print()
        print("  no comments yet")


def cmd_start(task_id: str) -> None:
    if not ensure_initialized():
        return

    result = find_task(task_id)
    if result is None:
        print(f"what task do you mean?")
        print(f"i do not find any task with id {task_id}")
        return

    task, file_path = result
    status = task.get("status")

    if status != STATUS_NOT_STARTED:
        started_time = task.get("started_time", "unknown")
        print(f"what was you doing until now? the task is already started at {_format_timestamp(started_time)}")
        return

    now = datetime.now()
    eta = task.get("eta")
    delta = _parse_eta(eta) if eta else None
    expected_end_time = (now + delta).strftime(TIMESTAMP_FORMAT) if delta else None

    update_task(task_id, file_path, {
        "status": STATUS_IN_PROGRESS,
        "started_time": now.strftime(TIMESTAMP_FORMAT),
        "expected_end_time": expected_end_time,
    })
    record_event(None, task_id, "started", now.strftime(TIMESTAMP_FORMAT))

    print(f"lets go. the task has been started")
    if eta:
        print(f"you have {eta} time to done this task")


def cmd_comment(task_id: str, message: str) -> None:
    if not ensure_initialized():
        return

    result = find_task(task_id)
    if result is None:
        print(f"No task found with id '{task_id}'.")
        return

    task, file_path = result
    now = datetime.now()
    comments = task.get("comments") or []
    comments.append({
        "text": message,
        "created_at": now.strftime(TIMESTAMP_FORMAT),
    })
    update_task(task_id, file_path, {"comments": comments})
    record_event(None, task_id, "commented", now.strftime(TIMESTAMP_FORMAT))
    print(f"Comment added to task '{task_id}'.")
