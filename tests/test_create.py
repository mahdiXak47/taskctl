"""
Tests for cmd_create — all scenarios a user can hit when creating a task.
"""

import pytest
from unittest.mock import patch

from taskctl.commands import cmd_create
from taskctl.database import db_get_task, db_get_task_last_event
from taskctl.models import STATUS_NOT_STARTED, STATUS_IN_PROGRESS


def _create(tmp_db, title="My Task", description="desc", eta=None, start=False):
    """Helper: call cmd_create with no interactive prompts."""
    with patch("taskctl.commands.ensure_initialized", return_value=True), \
         patch("taskctl.commands._prompt_eta", return_value=eta), \
         patch("taskctl.commands._prompt_start_now", return_value=start):
        cmd_create(title=title, description=description, eta=eta, start=start)


# ── Basic creation ────────────────────────────────────────────────────────────

class TestCreateBasic:
    def test_task_is_persisted(self, tmp_db, capsys):
        _create(tmp_db, title="Buy milk")
        from taskctl.database import db_tasks_in_range
        tasks = db_tasks_in_range(1)
        assert len(tasks) == 1
        assert tasks[0]["title"] == "Buy milk"

    def test_status_not_started_when_start_false(self, tmp_db, capsys):
        _create(tmp_db, title="T", start=False)
        from taskctl.database import db_tasks_in_range
        task = db_tasks_in_range(1)[0]
        assert task["status"] == STATUS_NOT_STARTED

    def test_status_in_progress_when_start_true(self, tmp_db, capsys):
        _create(tmp_db, title="T", start=True)
        from taskctl.database import db_tasks_in_range
        task = db_tasks_in_range(1)[0]
        assert task["status"] == STATUS_IN_PROGRESS

    def test_started_time_set_when_start_true(self, tmp_db, capsys):
        _create(tmp_db, title="T", start=True)
        from taskctl.database import db_tasks_in_range
        task = db_tasks_in_range(1)[0]
        assert task["started_time"] is not None

    def test_started_time_none_when_start_false(self, tmp_db, capsys):
        _create(tmp_db, title="T", start=False)
        from taskctl.database import db_tasks_in_range
        task = db_tasks_in_range(1)[0]
        assert task["started_time"] is None

    def test_description_is_stored(self, tmp_db, capsys):
        _create(tmp_db, title="T", description="My description")
        from taskctl.database import db_tasks_in_range
        task = db_tasks_in_range(1)[0]
        assert task["description"] == "My description"

    def test_output_contains_task_id(self, tmp_db, capsys):
        _create(tmp_db, title="T")
        out = capsys.readouterr().out
        assert "id:" in out

    def test_output_contains_title(self, tmp_db, capsys):
        _create(tmp_db, title="Special Title")
        out = capsys.readouterr().out
        assert "Special Title" in out


# ── ETA handling ──────────────────────────────────────────────────────────────

class TestCreateEta:
    def test_eta_stored(self, tmp_db, capsys):
        _create(tmp_db, title="T", eta="2h")
        from taskctl.database import db_tasks_in_range
        task = db_tasks_in_range(1)[0]
        assert task["eta"] == "2h"

    def test_expected_end_time_set_when_start_and_eta(self, tmp_db, capsys):
        _create(tmp_db, title="T", eta="1h", start=True)
        from taskctl.database import db_tasks_in_range
        task = db_tasks_in_range(1)[0]
        assert task["expected_end_time"] is not None

    def test_expected_end_time_none_when_not_started(self, tmp_db, capsys):
        _create(tmp_db, title="T", eta="1h", start=False)
        from taskctl.database import db_tasks_in_range
        task = db_tasks_in_range(1)[0]
        assert task["expected_end_time"] is None

    def test_due_by_shown_in_output_when_started_with_eta(self, tmp_db, capsys):
        _create(tmp_db, title="T", eta="1h", start=True)
        out = capsys.readouterr().out
        assert "Due by" in out

    def test_no_due_by_when_no_eta(self, tmp_db, capsys):
        _create(tmp_db, title="T", eta=None, start=True)
        out = capsys.readouterr().out
        assert "Due by" not in out


# ── Events ────────────────────────────────────────────────────────────────────

class TestCreateEvents:
    def test_created_event_recorded(self, tmp_db, capsys):
        _create(tmp_db, title="T")
        from taskctl.database import db_tasks_in_range, db_get_task_last_event
        task = db_tasks_in_range(1)[0]
        event = db_get_task_last_event(task["task_id"])
        assert event is not None
        assert event["event_type"] == "created"

    def test_started_event_recorded_when_start_true(self, tmp_db, capsys):
        _create(tmp_db, title="T", start=True)
        from taskctl.database import db_tasks_in_range
        import taskctl.database as db
        task = db_tasks_in_range(1)[0]
        with db.get_connection() as con:
            rows = con.execute(
                "SELECT event_type FROM events WHERE task_id = ? ORDER BY id",
                (task["task_id"],)
            ).fetchall()
        types = [r["event_type"] for r in rows]
        assert "created" in types
        assert "started" in types

    def test_no_started_event_when_start_false(self, tmp_db, capsys):
        _create(tmp_db, title="T", start=False)
        from taskctl.database import db_tasks_in_range
        import taskctl.database as db
        task = db_tasks_in_range(1)[0]
        with db.get_connection() as con:
            rows = con.execute(
                "SELECT event_type FROM events WHERE task_id = ?",
                (task["task_id"],)
            ).fetchall()
        types = [r["event_type"] for r in rows]
        assert "started" not in types
