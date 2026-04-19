"""
Tests for cmd_comment and cmd_describe.
"""

import pytest
from unittest.mock import patch

from taskctl.commands import cmd_comment, cmd_describe
from taskctl.database import db_insert_task, db_get_task
import taskctl.database as db
from taskctl.models import STATUS_NOT_STARTED, STATUS_IN_PROGRESS, TIMESTAMP_FORMAT
from tests.conftest import make_task, ts_str


def _insert(task: dict) -> str:
    db_insert_task(task)
    return task["task_id"]


# ══════════════════════════════════════════════════════════════════════════════
# cmd_comment
# ══════════════════════════════════════════════════════════════════════════════

class TestComment:
    def test_comment_is_persisted(self, tmp_db, capsys):
        tid = _insert(make_task(task_id="d0000001"))
        with patch("taskctl.commands.ensure_initialized", return_value=True):
            cmd_comment(tid, "hello world")
        task = db_get_task(tid)
        assert any(c["text"] == "hello world" for c in task["comments"])

    def test_multiple_comments_all_persisted(self, tmp_db, capsys):
        tid = _insert(make_task(task_id="d0000002"))
        with patch("taskctl.commands.ensure_initialized", return_value=True):
            cmd_comment(tid, "first")
            cmd_comment(tid, "second")
            cmd_comment(tid, "third")
        task = db_get_task(tid)
        texts = [c["text"] for c in task["comments"]]
        assert texts == ["first", "second", "third"]

    def test_comment_has_created_at_timestamp(self, tmp_db, capsys):
        tid = _insert(make_task(task_id="d0000003"))
        with patch("taskctl.commands.ensure_initialized", return_value=True):
            cmd_comment(tid, "check timestamp")
        task = db_get_task(tid)
        assert task["comments"][0]["created_at"] != ""

    def test_comment_on_nonexistent_task_prints_not_found(self, tmp_db, capsys):
        with patch("taskctl.commands.ensure_initialized", return_value=True):
            cmd_comment("doesntexist", "hello")
        assert "No task found" in capsys.readouterr().out

    def test_comment_prints_confirmation(self, tmp_db, capsys):
        tid = _insert(make_task(task_id="d0000004"))
        with patch("taskctl.commands.ensure_initialized", return_value=True):
            cmd_comment(tid, "msg")
        assert "Comment added" in capsys.readouterr().out

    def test_comment_records_commented_event(self, tmp_db, capsys):
        tid = _insert(make_task(task_id="d0000005"))
        with patch("taskctl.commands.ensure_initialized", return_value=True):
            cmd_comment(tid, "msg")
        event = db.get_connection().execute(
            "SELECT event_type FROM events WHERE task_id = ? AND event_type = 'commented'",
            (tid,)
        ).fetchone()
        assert event is not None


# ══════════════════════════════════════════════════════════════════════════════
# cmd_describe
# ══════════════════════════════════════════════════════════════════════════════

class TestDescribe:
    def test_shows_title_and_status(self, tmp_db, capsys):
        tid = _insert(make_task(task_id="e0000001", title="My Task", status=STATUS_NOT_STARTED))
        with patch("taskctl.commands.ensure_initialized", return_value=True):
            cmd_describe(tid)
        out = capsys.readouterr().out
        assert "My Task" in out
        assert STATUS_NOT_STARTED in out

    def test_nonexistent_task_prints_not_found(self, tmp_db, capsys):
        with patch("taskctl.commands.ensure_initialized", return_value=True):
            cmd_describe("doesntexist")
        assert "do not find" in capsys.readouterr().out

    def test_no_deadline_shows_no_deadline_set(self, tmp_db, capsys):
        tid = _insert(make_task(task_id="e0000002", expected_end_time=None))
        with patch("taskctl.commands.ensure_initialized", return_value=True):
            cmd_describe(tid)
        assert "no deadline set" in capsys.readouterr().out

    def test_with_deadline_shows_time_remaining(self, tmp_db, capsys):
        future = ts_str(__import__("datetime").timedelta(hours=3))
        tid = _insert(make_task(task_id="e0000003", expected_end_time=future))
        with patch("taskctl.commands.ensure_initialized", return_value=True):
            cmd_describe(tid)
        out = capsys.readouterr().out
        assert "Time remaining" in out
        assert "no deadline set" not in out

    def test_no_comments_shows_no_comments_yet(self, tmp_db, capsys):
        tid = _insert(make_task(task_id="e0000004", comments=[]))
        with patch("taskctl.commands.ensure_initialized", return_value=True):
            cmd_describe(tid)
        assert "no comments yet" in capsys.readouterr().out

    def test_shows_last_5_comments_by_default(self, tmp_db, capsys):
        tid = _insert(make_task(task_id="e0000005"))
        now = ts_str()
        # insert 7 comments directly
        with patch("taskctl.commands.ensure_initialized", return_value=True):
            for i in range(1, 8):
                cmd_comment(tid, f"comment {i}")
        capsys.readouterr()   # clear output from cmd_comment calls

        with patch("taskctl.commands.ensure_initialized", return_value=True):
            cmd_describe(tid)
        out = capsys.readouterr().out
        # last 5 should appear, first 2 should not
        assert "comment 7" in out
        assert "comment 3" in out
        assert "comment 1" not in out
        assert "comment 2" not in out

    def test_verbose_shows_all_comments(self, tmp_db, capsys):
        tid = _insert(make_task(task_id="e0000006"))
        with patch("taskctl.commands.ensure_initialized", return_value=True):
            for i in range(1, 8):
                cmd_comment(tid, f"comment {i}")
        capsys.readouterr()

        with patch("taskctl.commands.ensure_initialized", return_value=True):
            cmd_describe(tid, verbose=True)
        out = capsys.readouterr().out
        assert "comment 1" in out
        assert "comment 7" in out

    def test_shows_truncation_hint_when_more_than_5(self, tmp_db, capsys):
        tid = _insert(make_task(task_id="e0000007"))
        with patch("taskctl.commands.ensure_initialized", return_value=True):
            for i in range(6):
                cmd_comment(tid, f"msg {i}")
        capsys.readouterr()

        with patch("taskctl.commands.ensure_initialized", return_value=True):
            cmd_describe(tid)
        assert "showing last 5" in capsys.readouterr().out

    def test_no_truncation_hint_when_5_or_fewer(self, tmp_db, capsys):
        tid = _insert(make_task(task_id="e0000008"))
        with patch("taskctl.commands.ensure_initialized", return_value=True):
            for i in range(3):
                cmd_comment(tid, f"msg {i}")
        capsys.readouterr()

        with patch("taskctl.commands.ensure_initialized", return_value=True):
            cmd_describe(tid)
        assert "showing last 5" not in capsys.readouterr().out

    def test_breached_deadline_shows_breached_in_remaining(self, tmp_db, capsys):
        past = ts_str(__import__("datetime").timedelta(hours=-2))
        tid = _insert(make_task(task_id="e0000009", expected_end_time=past))
        with patch("taskctl.commands.ensure_initialized", return_value=True):
            cmd_describe(tid)
        assert "breached" in capsys.readouterr().out
