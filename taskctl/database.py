"""
Single SQLite database for taskctl.
DB file: ~/.taskctl/taskctl.db

Tables:
  users    — registered accounts
  tasks    — all tasks
  comments — task comments (one row per comment)
"""

import sqlite3
from pathlib import Path

TASKCTL_DIR = Path.home() / ".taskctl"
DB_PATH = TASKCTL_DIR / "taskctl.db"


def get_connection() -> sqlite3.Connection:
    TASKCTL_DIR.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA foreign_keys=ON")
    return con


def init_db() -> None:
    """Create tables if they don't exist yet."""
    with get_connection() as con:
        con.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                username      TEXT PRIMARY KEY,
                password_hash TEXT NOT NULL,
                salt          TEXT NOT NULL,
                first_name    TEXT NOT NULL DEFAULT '',
                last_name     TEXT NOT NULL DEFAULT '',
                email         TEXT NOT NULL DEFAULT '',
                created_at    TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS tasks (
                task_id           TEXT PRIMARY KEY,
                title             TEXT NOT NULL,
                description       TEXT NOT NULL DEFAULT '',
                eta               TEXT,
                created_time      TEXT NOT NULL,
                started_time      TEXT,
                expected_end_time TEXT,
                end_time          TEXT,
                status            TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS comments (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id    TEXT NOT NULL REFERENCES tasks(task_id) ON DELETE CASCADE,
                text       TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS events (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id    TEXT REFERENCES users(username) ON DELETE SET NULL,
                task_id    TEXT NOT NULL,
                event_type VARCHAR(32) NOT NULL,
                timestamp  VARCHAR(20) NOT NULL
            );
        """)


# ── User operations ───────────────────────────────────────────────────────────

def db_user_exists(username: str) -> bool:
    with get_connection() as con:
        row = con.execute(
            "SELECT 1 FROM users WHERE username = ?", (username,)
        ).fetchone()
    return row is not None


def db_insert_user(
    username: str,
    password_hash: str,
    salt: str,
    first_name: str = "",
    last_name: str = "",
    email: str = "",
    created_at: str = "",
) -> None:
    with get_connection() as con:
        con.execute(
            """INSERT INTO users (username, password_hash, salt, first_name, last_name, email, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (username, password_hash, salt, first_name, last_name, email, created_at),
        )


def db_get_user(username: str) -> dict | None:
    with get_connection() as con:
        row = con.execute(
            "SELECT * FROM users WHERE username = ?", (username,)
        ).fetchone()
    return dict(row) if row else None


# ── Task operations ───────────────────────────────────────────────────────────

def _row_to_task(row: sqlite3.Row, comments: list[dict]) -> dict:
    return {
        "task_id":           row["task_id"],
        "title":             row["title"],
        "description":       row["description"],
        "eta":               row["eta"],
        "created_time":      row["created_time"],
        "started_time":      row["started_time"],
        "expected_end_time": row["expected_end_time"],
        "end_time":          row["end_time"],
        "status":            row["status"],
        "comments":          comments,
    }


def _load_comments(con: sqlite3.Connection, task_id: str) -> list[dict]:
    rows = con.execute(
        "SELECT text, created_at FROM comments WHERE task_id = ? ORDER BY id",
        (task_id,),
    ).fetchall()
    return [{"text": r["text"], "created_at": r["created_at"]} for r in rows]


def db_insert_task(task: dict) -> None:
    with get_connection() as con:
        con.execute(
            """INSERT INTO tasks
               (task_id, title, description, eta, created_time,
                started_time, expected_end_time, end_time, status)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                task["task_id"],
                task["title"],
                task.get("description") or "",
                task.get("eta"),
                task["created_time"],
                task.get("started_time"),
                task.get("expected_end_time"),
                task.get("end_time"),
                task["status"],
            ),
        )
        # insert any initial comments (usually empty on create)
        for c in task.get("comments") or []:
            text       = c if isinstance(c, str) else c.get("text", "")
            created_at = "" if isinstance(c, str) else c.get("created_at", "")
            con.execute(
                "INSERT INTO comments (task_id, text, created_at) VALUES (?, ?, ?)",
                (task["task_id"], text, created_at),
            )


def db_get_task(task_id: str) -> dict | None:
    with get_connection() as con:
        row = con.execute(
            "SELECT * FROM tasks WHERE task_id = ?", (task_id,)
        ).fetchone()
        if not row:
            return None
        comments = _load_comments(con, task_id)
    return _row_to_task(row, comments)


def db_tasks_in_range(days: int) -> list[dict]:
    """Return tasks created within the last `days` days, newest first."""
    with get_connection() as con:
        rows = con.execute(
            """SELECT * FROM tasks
               WHERE SUBSTR(REPLACE(created_time, '/', '-'), 1, 10) >= DATE('now', ?)
               ORDER BY created_time DESC""",
            (f"-{days} days",),
        ).fetchall()
        result = []
        for row in rows:
            comments = _load_comments(con, row["task_id"])
            result.append(_row_to_task(row, comments))
    return result


def db_update_task(task_id: str, changes: dict) -> None:
    """Apply a dict of column→value changes to a task row."""
    comments = changes.pop("comments", None)
    if changes:
        cols = ", ".join(f"{k} = ?" for k in changes)
        vals = list(changes.values()) + [task_id]
        with get_connection() as con:
            con.execute(f"UPDATE tasks SET {cols} WHERE task_id = ?", vals)
    if comments is not None:
        with get_connection() as con:
            con.execute("DELETE FROM comments WHERE task_id = ?", (task_id,))
            for c in comments:
                text       = c if isinstance(c, str) else c.get("text", "")
                created_at = "" if isinstance(c, str) else c.get("created_at", "")
                con.execute(
                    "INSERT INTO comments (task_id, text, created_at) VALUES (?, ?, ?)",
                    (task_id, text, created_at),
                )


def db_delete_task(task_id: str) -> None:
    with get_connection() as con:
        con.execute("DELETE FROM tasks WHERE task_id = ?", (task_id,))


# ── Event operations ──────────────────────────────────────────────────────────

def db_insert_event(user_id: str | None, task_id: str, event_type: str, timestamp: str) -> None:
    with get_connection() as con:
        con.execute(
            "INSERT INTO events (user_id, task_id, event_type, timestamp) VALUES (?, ?, ?, ?)",
            (user_id, task_id, event_type, timestamp),
        )


def db_get_task_last_event(task_id: str) -> dict | None:
    with get_connection() as con:
        row = con.execute(
            """SELECT * FROM events WHERE task_id = ?
               ORDER BY timestamp DESC, id DESC LIMIT 1""",
            (task_id,),
        ).fetchone()
    return dict(row) if row else None


def db_get_user_events(user_id: str) -> list[dict]:
    with get_connection() as con:
        rows = con.execute(
            "SELECT * FROM events WHERE user_id = ? ORDER BY timestamp DESC",
            (user_id,),
        ).fetchall()
    return [dict(r) for r in rows]
