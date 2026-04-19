"""
Tests for pure helper functions: _parse_eta, _format_timestamp, _format_remaining.
These do not touch the database.
"""

import re
from datetime import datetime, timedelta
from unittest.mock import patch

import pytest

from taskctl.commands import _parse_eta, _format_timestamp, _format_remaining
from taskctl.models import TIMESTAMP_FORMAT

# ── Fixed reference time used to make timestamp tests deterministic ───────────

FIXED_NOW = datetime(2026, 4, 15, 20, 0, 0)   # Wednesday, 8 PM


class _FixedDatetime(datetime):
    """datetime subclass whose .now() always returns FIXED_NOW."""
    @classmethod
    def now(cls, tz=None):
        return FIXED_NOW


def fixed_time():
    """Patch taskctl.commands.datetime so .now() is deterministic."""
    return patch("taskctl.commands.datetime", _FixedDatetime)


def make_ts(dt: datetime) -> str:
    return dt.strftime(TIMESTAMP_FORMAT)


# ── _parse_eta ────────────────────────────────────────────────────────────────

class TestParseEta:
    def test_minutes_valid(self):
        assert _parse_eta("30m") == timedelta(minutes=30)

    def test_hours_valid(self):
        assert _parse_eta("2h") == timedelta(hours=2)

    def test_days_valid(self):
        assert _parse_eta("3d") == timedelta(days=3)

    def test_minimum_boundary_allowed(self):
        assert _parse_eta("5m") == timedelta(minutes=5)

    def test_maximum_boundary_allowed(self):
        assert _parse_eta("7d") == timedelta(days=7)

    def test_below_minimum_rejected(self):
        assert _parse_eta("4m") is None

    def test_above_maximum_rejected(self):
        assert _parse_eta("8d") is None

    def test_unknown_unit_rejected(self):
        assert _parse_eta("10x") is None

    def test_non_numeric_value_rejected(self):
        assert _parse_eta("abm") is None

    def test_empty_string_returns_none(self):
        assert _parse_eta("") is None

    def test_none_returns_none(self):
        assert _parse_eta(None) is None


# ── _format_timestamp ─────────────────────────────────────────────────────────

class TestFormatTimestamp:
    def test_30_seconds_ago_shows_1_minute_ago(self):
        with fixed_time():
            ts = make_ts(FIXED_NOW - timedelta(seconds=30))
            assert _format_timestamp(ts) == "1 minute ago"

    def test_1_minute_ago(self):
        with fixed_time():
            ts = make_ts(FIXED_NOW - timedelta(minutes=1))
            assert _format_timestamp(ts) == "1 minute ago"

    def test_5_minutes_ago(self):
        with fixed_time():
            ts = make_ts(FIXED_NOW - timedelta(minutes=5))
            assert _format_timestamp(ts) == "5 minutes ago"

    def test_59_minutes_ago(self):
        with fixed_time():
            ts = make_ts(FIXED_NOW - timedelta(minutes=59))
            assert _format_timestamp(ts) == "59 minutes ago"

    def test_1_hour_ago(self):
        with fixed_time():
            ts = make_ts(FIXED_NOW - timedelta(hours=1))
            assert _format_timestamp(ts) == "1 hour ago"

    def test_3_hours_ago(self):
        with fixed_time():
            ts = make_ts(FIXED_NOW - timedelta(hours=3))
            assert _format_timestamp(ts) == "3 hours ago"

    def test_exactly_12_hours_ago_shows_today(self):
        # 12h is NOT in the "hours ago" bucket (< not <=), falls through to date
        with fixed_time():
            ts = make_ts(FIXED_NOW - timedelta(hours=12))  # 08:00 same day
            assert _format_timestamp(ts) == "today 08:00"

    def test_13_hours_ago_same_day_shows_today(self):
        with fixed_time():
            ts = make_ts(FIXED_NOW - timedelta(hours=13))  # 07:00 same day
            assert _format_timestamp(ts) == "today 07:00"

    def test_yesterday(self):
        with fixed_time():
            ts = make_ts(FIXED_NOW - timedelta(days=1))
            assert _format_timestamp(ts) == "yesterday 20:00"

    def test_3_days_ago_shows_original_format(self):
        with fixed_time():
            ts = make_ts(FIXED_NOW - timedelta(days=3))
            assert _format_timestamp(ts) == ts   # original returned unchanged

    def test_future_within_today_shows_today(self):
        # Bug: before the fix this returned "-2 hours ago"
        with fixed_time():
            ts = make_ts(FIXED_NOW + timedelta(hours=2))   # 22:00 same day
            assert _format_timestamp(ts) == "today 22:00"

    def test_future_tomorrow_shows_tomorrow(self):
        with fixed_time():
            ts = make_ts(FIXED_NOW + timedelta(days=1))
            assert _format_timestamp(ts) == "tomorrow 20:00"

    def test_future_far_shows_original_format(self):
        with fixed_time():
            ts = make_ts(FIXED_NOW + timedelta(days=5))
            assert _format_timestamp(ts) == ts

    def test_empty_string_returns_empty(self):
        assert _format_timestamp("") == ""

    def test_invalid_string_returns_original(self):
        assert _format_timestamp("not-a-date") == "not-a-date"

    def test_none_returns_empty(self):
        assert _format_timestamp(None) == ""


# ── _format_remaining ─────────────────────────────────────────────────────────

class TestFormatRemaining:
    def test_2_hours_remaining(self):
        with fixed_time():
            due = make_ts(FIXED_NOW + timedelta(hours=2))
            assert _format_remaining(due) == "2h"

    def test_1_day_3_hours_remaining(self):
        with fixed_time():
            due = make_ts(FIXED_NOW + timedelta(days=1, hours=3))
            assert _format_remaining(due) == "1d 3h"

    def test_breached_by_30_minutes(self):
        with fixed_time():
            due = make_ts(FIXED_NOW - timedelta(minutes=30))
            assert _format_remaining(due) == "deadline breached by 30m"

    def test_breached_by_1_day(self):
        with fixed_time():
            due = make_ts(FIXED_NOW - timedelta(days=1))
            assert _format_remaining(due) == "deadline breached by 1d"

    def test_invalid_returns_no_deadline_set(self):
        assert _format_remaining(None) == "no deadline set"
        assert _format_remaining("bad-format") == "no deadline set"
