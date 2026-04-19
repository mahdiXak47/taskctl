"""
Tests for cmd_start, cmd_done, cmd_delete.
"""

import pytest
from unittest.mock import patch

from taskctl.commands import cmd_start, cmd_done, cmd_delete
from taskctl.database import db_insert_task, db_get_task, db_tasks_in_range
import taskctl.database as db
from taskctl.models import (
    TIMESTAMP_FORMAT,
    STATUS_NOT_STARTED,
    STATUS_IN_PROGRESS,
    STATUS_BREACHED_DEADLINE,
    STATUS_DONE_INTIME,
    STATUS_DONE_BUT_BREACHED,
)
from tests.conftest import make_task, ts_str


def _insert(task: dict) -> str:
    db_insert_task(task)
    return task["task_id"]


# ══════════════════════════════════════════════════════════════════════════════
# cmd_start
# ══════════════════════════════════════════════════════════════════════════════

class TestStart:
    def test_start_not_started_task_succeeds(self, tmp_db, capsys):
        tid = _insert(make_task(task_id="aaa00001", status=STATUS_NOT_STARTED))
        with patch("taskctl.commands.ensure_initialized", return_value=True):
            cmd_start(tid)
        task = db_get_task(tid)
        assert task["status"] == STATUS_IN_PROGRESS
        assert task["started_time"] is not None

    def test_start_sets_expected_end_time_when_eta_present(self, tmp_db, capsys):
        tid = _insert(make_task(task_id="aaa00002", status=STATUS_NOT_STARTED, eta="2h"))
        with patch("taskctl.commands.ensure_initialized", return_value=True):
            cmd_start(tid)
        task = db_get_task(tid)
        assert task["expected_end_time"] is not None

    def test_start_no_expected_end_time_without_eta(self, tmp_db, capsys):
        tid = _insert(make_task(task_id="aaa00003", status=STATUS_NOT_STARTED, eta=None))
        with patch("taskctl.commands.ensure_initialized", return_value=True):
            cmd_start(tid)
        task = db_get_task(tid)
        assert task["expected_end_time"] is None

    def test_start_prints_lets_go(self, tmp_db, capsys):
        tid = _insert(make_task(task_id="aaa00004", status=STATUS_NOT_STARTED))
        with patch("taskctl.commands.ensure_initialized", return_value=True):
            cmd_start(tid)
        assert "lets go" in capsys.readouterr().out

    def test_start_prints_eta_if_present(self, tmp_db, capsys):
        tid = _insert(make_task(task_id="aaa00005", status=STATUS_NOT_STARTED, eta="3h"))
        with patch("taskctl.commands.ensure_initialized", return_value=True):
            cmd_start(tid)
        assert "3h" in capsys.readouterr().out

    def test_start_already_in_progress_prints_warning(self, tmp_db, capsys):
        tid = _insert(make_task(
            task_id="aaa00006",
            status=STATUS_IN_PROGRESS,
            started_time=ts_str(),
        ))
        with patch("taskctl.commands.ensure_initialized", return_value=True):
            cmd_start(tid)
        assert "already started" in capsys.readouterr().out

    def test_start_already_in_progress_does_not_change_status(self, tmp_db, capsys):
        original_start = ts_str()
        tid = _insert(make_task(
            task_id="aaa00007",
            status=STATUS_IN_PROGRESS,
            started_time=original_start,
        ))
        with patch("taskctl.commands.ensure_initialized", return_value=True):
            cmd_start(tid)
        task = db_get_task(tid)
        assert task["started_time"] == original_start

    def test_start_nonexistent_task_prints_not_found(self, tmp_db, capsys):
        with patch("taskctl.commands.ensure_initialized", return_value=True):
            cmd_start("doesntexist")
        assert "do not find" in capsys.readouterr().out

    def test_start_records_started_event(self, tmp_db, capsys):
        tid = _insert(make_task(task_id="aaa00008", status=STATUS_NOT_STARTED))
        with patch("taskctl.commands.ensure_initialized", return_value=True):
            cmd_start(tid)
        event = db.get_connection().execute(
            "SELECT event_type FROM events WHERE task_id = ? AND event_type = 'started'",
            (tid,)
        ).fetchone()
        assert event is not None


# ══════════════════════════════════════════════════════════════════════════════
# cmd_done
# ══════════════════════════════════════════════════════════════════════════════

class TestDone:
    def test_done_in_progress_marks_done_intime(self, tmp_db, capsys):
        tid = _insert(make_task(
            task_id="bbb00001",
            status=STATUS_IN_PROGRESS,
            started_time=ts_str(),
        ))
        with patch("taskctl.commands.ensure_initialized", return_value=True):
            cmd_done(tid)
        assert db_get_task(tid)["status"] == STATUS_DONE_INTIME

    def test_done_breached_deadline_marks_done_but_breached(self, tmp_db, capsys):
        tid = _insert(make_task(
            task_id="bbb00002",
            status=STATUS_BREACHED_DEADLINE,
            started_time=ts_str(),
        ))
        with patch("taskctl.commands.ensure_initialized", return_value=True):
            cmd_done(tid)
        assert db_get_task(tid)["status"] == STATUS_DONE_BUT_BREACHED

    def test_done_sets_end_time(self, tmp_db, capsys):
        tid = _insert(make_task(
            task_id="bbb00003",
            status=STATUS_IN_PROGRESS,
            started_time=ts_str(),
        ))
        with patch("taskctl.commands.ensure_initialized", return_value=True):
            cmd_done(tid)
        assert db_get_task(tid)["end_time"] is not None

    def test_done_not_started_task_prints_warning(self, tmp_db, capsys):
        tid = _insert(make_task(task_id="bbb00004", status=STATUS_NOT_STARTED))
        with patch("taskctl.commands.ensure_initialized", return_value=True):
            cmd_done(tid)
        assert "not been started" in capsys.readouterr().out

    def test_done_not_started_task_does_not_change_status(self, tmp_db, capsys):
        tid = _insert(make_task(task_id="bbb00005", status=STATUS_NOT_STARTED))
        with patch("taskctl.commands.ensure_initialized", return_value=True):
            cmd_done(tid)
        assert db_get_task(tid)["status"] == STATUS_NOT_STARTED

    def test_done_already_done_intime_prints_warning(self, tmp_db, capsys):
        tid = _insert(make_task(
            task_id="bbb00006",
            status=STATUS_DONE_INTIME,
            started_time=ts_str(),
            end_time=ts_str(),
        ))
        with patch("taskctl.commands.ensure_initialized", return_value=True):
            cmd_done(tid)
        assert "already" in capsys.readouterr().out

    def test_done_nonexistent_task_prints_not_found(self, tmp_db, capsys):
        with patch("taskctl.commands.ensure_initialized", return_value=True):
            cmd_done("doesntexist")
        assert "No task found" in capsys.readouterr().out

    def test_done_intime_prints_great_message(self, tmp_db, capsys):
        tid = _insert(make_task(
            task_id="bbb00007",
            status=STATUS_IN_PROGRESS,
            started_time=ts_str(),
        ))
        with patch("taskctl.commands.ensure_initialized", return_value=True):
            cmd_done(tid)
        assert "Great" in capsys.readouterr().out

    def test_done_breached_prints_not_bad_message(self, tmp_db, capsys):
        tid = _insert(make_task(
            task_id="bbb00008",
            status=STATUS_BREACHED_DEADLINE,
            started_time=ts_str(),
        ))
        with patch("taskctl.commands.ensure_initialized", return_value=True):
            cmd_done(tid)
        assert "Not bad" in capsys.readouterr().out

    def test_done_records_is_done_event(self, tmp_db, capsys):
        tid = _insert(make_task(
            task_id="bbb00009",
            status=STATUS_IN_PROGRESS,
            started_time=ts_str(),
        ))
        with patch("taskctl.commands.ensure_initialized", return_value=True):
            cmd_done(tid)
        event = db.get_connection().execute(
            "SELECT event_type FROM events WHERE task_id = ? AND event_type = 'is done'",
            (tid,)
        ).fetchone()
        assert event is not None


# ══════════════════════════════════════════════════════════════════════════════
# cmd_delete
# ══════════════════════════════════════════════════════════════════════════════

class TestDelete:
    def test_delete_not_started_task_removes_it(self, tmp_db, capsys):
        tid = _insert(make_task(task_id="ccc00001", status=STATUS_NOT_STARTED))
        with patch("taskctl.commands.ensure_initialized", return_value=True):
            cmd_delete(tid)
        assert db_get_task(tid) is None

    def test_delete_done_task_removes_it(self, tmp_db, capsys):
        tid = _insert(make_task(
            task_id="ccc00002",
            status=STATUS_DONE_INTIME,
            started_time=ts_str(),
            end_time=ts_str(),
        ))
        with patch("taskctl.commands.ensure_initialized", return_value=True):
            cmd_delete(tid)
        assert db_get_task(tid) is None

    def test_delete_in_progress_with_confirmation_removes_it(self, tmp_db, capsys):
        tid = _insert(make_task(
            task_id="ccc00003",
            status=STATUS_IN_PROGRESS,
            started_time=ts_str(),
        ))
        with patch("taskctl.commands.ensure_initialized", return_value=True), \
             patch("builtins.input", return_value="y"):
            cmd_delete(tid)
        assert db_get_task(tid) is None

    def test_delete_in_progress_cancelled_keeps_task(self, tmp_db, capsys):
        tid = _insert(make_task(
            task_id="ccc00004",
            status=STATUS_IN_PROGRESS,
            started_time=ts_str(),
        ))
        with patch("taskctl.commands.ensure_initialized", return_value=True), \
             patch("builtins.input", return_value="n"):
            cmd_delete(tid)
        assert db_get_task(tid) is not None

    def test_delete_in_progress_cancelled_prints_cancellation(self, tmp_db, capsys):
        tid = _insert(make_task(
            task_id="ccc00005",
            status=STATUS_IN_PROGRESS,
            started_time=ts_str(),
        ))
        with patch("taskctl.commands.ensure_initialized", return_value=True), \
             patch("builtins.input", return_value="n"):
            cmd_delete(tid)
        assert "cancelled" in capsys.readouterr().out

    def test_delete_nonexistent_task_prints_not_found(self, tmp_db, capsys):
        with patch("taskctl.commands.ensure_initialized", return_value=True):
            cmd_delete("doesntexist")
        assert "No task found" in capsys.readouterr().out

    def test_delete_records_deleted_event(self, tmp_db, capsys):
        tid = _insert(make_task(task_id="ccc00006", status=STATUS_NOT_STARTED))
        with patch("taskctl.commands.ensure_initialized", return_value=True):
            cmd_delete(tid)
        # task is gone but event must survive (no CASCADE on events.task_id)
        event = db.get_connection().execute(
            "SELECT event_type FROM events WHERE task_id = ? AND event_type = 'deleted'",
            (tid,)
        ).fetchone()
        assert event is not None

    def test_delete_prints_deleted_confirmation(self, tmp_db, capsys):
        tid = _insert(make_task(task_id="ccc00007", status=STATUS_NOT_STARTED))
        with patch("taskctl.commands.ensure_initialized", return_value=True):
            cmd_delete(tid)
        assert "deleted" in capsys.readouterr().out
