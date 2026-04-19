"""
Shared fixtures and helpers for all taskctl tests.

Every test that touches the DB must request the `tmp_db` fixture so that
operations go to a throwaway SQLite file instead of ~/.taskctl/taskctl.db.
"""

import pytest
from datetime import datetime, timedelta
from pathlib import Path

import taskctl.database as db_module
import taskctl.storage as storage_module
import taskctl.auth_store as auth_module
from taskctl.models import TIMESTAMP_FORMAT, STATUS_NOT_STARTED, STATUS_IN_PROGRESS


# ── Helpers ───────────────────────────────────────────────────────────────────

def ts_str(delta: timedelta = timedelta(0)) -> str:
    """TIMESTAMP_FORMAT string offset from now (e.g. ts_str(timedelta(hours=-2)))."""
    return (datetime.now() + delta).strftime(TIMESTAMP_FORMAT)


def make_task(**overrides) -> dict:
    """Return a task dict with sensible defaults. Pass keyword args to override."""
    base = {
        "task_id": "test1234",
        "title": "Test Task",
        "description": "A test description",
        "comments": [],
        "eta": None,
        "created_time": ts_str(),
        "started_time": None,
        "expected_end_time": None,
        "end_time": None,
        "status": STATUS_NOT_STARTED,
    }
    base.update(overrides)
    return base


# ── Fixture ───────────────────────────────────────────────────────────────────

@pytest.fixture
def tmp_db(tmp_path, monkeypatch):
    """
    Redirect all DB I/O to a temporary directory.
    The directory already exists (pytest creates tmp_path), so
    ensure_initialized() will not prompt for confirmation.
    """
    db_path = tmp_path / "taskctl.db"
    monkeypatch.setattr(db_module,      "TASKCTL_DIR", tmp_path)
    monkeypatch.setattr(db_module,      "DB_PATH",     db_path)
    monkeypatch.setattr(storage_module, "TASKCTL_DIR", tmp_path)
    monkeypatch.setattr(auth_module,    "TASKCTL_DIR", tmp_path)
    monkeypatch.setattr(auth_module,    "SECRET_FILE", tmp_path / "secret.key")
    db_module.init_db()
    yield tmp_path
