"""
Tests for cmd_list — duration, status filter, verbose flag, edge cases.
"""

import pytest
from unittest.mock import patch
from datetime import datetime, timedelta

from taskctl.commands import cmd_list
from taskctl.database import db_insert_task
from taskctl.models import (
    TIMESTAMP_FORMAT,
    STATUS_NOT_STARTED,
    STATUS_IN_PROGRESS,
    STATUS_DONE_INTIME,
    STATUS_BREACHED_DEADLINE,
    STATUS_DONE_BUT_BREACHED,
)
from tests.conftest import make_task, ts_str


def _insert(task: dict) -> str:
    db_insert_task(task)
    return task["task_id"]


def _list(tmp_db, duration=None, status=None, verbose=False):
    with patch("taskctl.commands.ensure_initialized", return_value=True):
        cmd_list(duration=duration, status=status, verbose=verbose)


# ── Basic listing ─────────────────────────────────────────────────────────────

class TestListBasic:
    def test_empty_db_prints_no_tasks_found(self, tmp_db, capsys):
        _list(tmp_db)
        assert "No tasks found" in capsys.readouterr().out

    def test_single_task_appears_in_output(self, tmp_db, capsys):
        _insert(make_task(task_id="f0000001", title="My Task"))
        _list(tmp_db)
        assert "My Task" in capsys.readouterr().out

    def test_task_id_appears_in_output(self, tmp_db, capsys):
        _insert(make_task(task_id="f0000002", title="T"))
        _list(tmp_db)
        assert "f0000002" in capsys.readouterr().out

    def test_status_appears_in_output(self, tmp_db, capsys):
        _insert(make_task(task_id="f0000003", status=STATUS_IN_PROGRESS))
        _list(tmp_db)
        assert STATUS_IN_PROGRESS in capsys.readouterr().out

    def test_multiple_tasks_all_listed(self, tmp_db, capsys):
        _insert(make_task(task_id="f0000004", title="Alpha"))
        _insert(make_task(task_id="f0000005", title="Beta"))
        _list(tmp_db)
        out = capsys.readouterr().out
        assert "Alpha" in out
        assert "Beta" in out

    def test_old_task_not_shown_with_default_duration(self, tmp_db, capsys):
        # created 3 days ago — outside the default 1-day window
        old_ts = (datetime.now() - timedelta(days=3)).strftime(TIMESTAMP_FORMAT)
        _insert(make_task(task_id="f0000006", title="OldTask", created_time=old_ts))
        _list(tmp_db)
        assert "OldTask" not in capsys.readouterr().out


# ── Duration filter ───────────────────────────────────────────────────────────

class TestListDuration:
    def test_7d_includes_task_from_3_days_ago(self, tmp_db, capsys):
        old_ts = (datetime.now() - timedelta(days=3)).strftime(TIMESTAMP_FORMAT)
        _insert(make_task(task_id="g0000001", title="OldTask", created_time=old_ts))
        _list(tmp_db, duration="7d")
        assert "OldTask" in capsys.readouterr().out

    def test_invalid_duration_prints_error(self, tmp_db, capsys):
        _list(tmp_db, duration="99x")
        assert "Invalid duration" in capsys.readouterr().out

    def test_invalid_duration_lists_nothing(self, tmp_db, capsys):
        _insert(make_task(task_id="g0000002", title="T"))
        _list(tmp_db, duration="99x")
        out = capsys.readouterr().out
        assert "T" not in out


# ── Status filter ─────────────────────────────────────────────────────────────

class TestListStatus:
    def test_filter_shows_only_matching_status(self, tmp_db, capsys):
        _insert(make_task(task_id="h0000001", title="Active", status=STATUS_IN_PROGRESS))
        _insert(make_task(task_id="h0000002", title="Idle",   status=STATUS_NOT_STARTED))
        _list(tmp_db, status=STATUS_IN_PROGRESS)
        out = capsys.readouterr().out
        assert "Active" in out
        assert "Idle" not in out

    def test_filter_no_match_prints_no_tasks_found(self, tmp_db, capsys):
        _insert(make_task(task_id="h0000003", status=STATUS_NOT_STARTED))
        _list(tmp_db, status=STATUS_DONE_INTIME)
        assert "No tasks found" in capsys.readouterr().out

    def test_invalid_status_prints_error(self, tmp_db, capsys):
        _list(tmp_db, status="flying")
        assert "Unknown status" in capsys.readouterr().out

    def test_invalid_status_shows_valid_values(self, tmp_db, capsys):
        _list(tmp_db, status="flying")
        assert "Valid values" in capsys.readouterr().out

    def test_all_valid_statuses_accepted(self, tmp_db, capsys):
        valid = (
            STATUS_NOT_STARTED, STATUS_IN_PROGRESS, STATUS_BREACHED_DEADLINE,
            STATUS_DONE_INTIME, STATUS_DONE_BUT_BREACHED,
        )
        for s in valid:
            with patch("taskctl.commands.ensure_initialized", return_value=True):
                cmd_list(duration=None, status=s, verbose=False)
            out = capsys.readouterr().out
            assert "Unknown status" not in out


# ── Verbose flag ──────────────────────────────────────────────────────────────

class TestListVerbose:
    def test_verbose_shows_event_column_header(self, tmp_db, capsys):
        _insert(make_task(task_id="i0000001", title="T"))
        _list(tmp_db, verbose=True)
        assert "EVENT" in capsys.readouterr().out

    def test_non_verbose_has_no_event_column(self, tmp_db, capsys):
        _insert(make_task(task_id="i0000002", title="T"))
        _list(tmp_db, verbose=False)
        assert "EVENT" not in capsys.readouterr().out

    def test_verbose_shows_created_event_after_create(self, tmp_db, capsys):
        from taskctl.commands import cmd_create
        with patch("taskctl.commands.ensure_initialized", return_value=True), \
             patch("taskctl.commands._prompt_eta", return_value=None), \
             patch("taskctl.commands._prompt_start_now", return_value=False):
            cmd_create(title="ETask", description="", eta=None, start=False)
        capsys.readouterr()
        _list(tmp_db, verbose=True)
        assert "created" in capsys.readouterr().out

    def test_verbose_shows_started_event_after_start(self, tmp_db, capsys):
        from taskctl.commands import cmd_create, cmd_start
        with patch("taskctl.commands.ensure_initialized", return_value=True), \
             patch("taskctl.commands._prompt_eta", return_value=None), \
             patch("taskctl.commands._prompt_start_now", return_value=False):
            cmd_create(title="STask", description="", eta=None, start=False)
        from taskctl.database import db_tasks_in_range
        tid = db_tasks_in_range(1)[0]["task_id"]
        capsys.readouterr()
        with patch("taskctl.commands.ensure_initialized", return_value=True):
            cmd_start(tid)
        capsys.readouterr()
        _list(tmp_db, verbose=True)
        assert "started" in capsys.readouterr().out
