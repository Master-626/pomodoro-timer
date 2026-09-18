import pytest
from pomodoro_timer.tracker import PomodoroTracker, Session


def test_start_focus_session(tmp_path):
    """Test starting a focus session."""
    tracker = PomodoroTracker(str(tmp_path / "sessions.json"))
    session = tracker.start_focus_session(duration_minutes=25)
    assert session.type == "focus"
    assert session.duration_minutes == 25
    assert len(tracker.sessions) == 1


def test_start_break(tmp_path):
    """Test starting a break."""
    tracker = PomodoroTracker(str(tmp_path / "sessions.json"))
    session = tracker.start_break(break_type="short", duration_minutes=5)
    assert session.type == "short_break"
    assert session.duration_minutes == 5


def test_get_stats(tmp_path):
    """Test getting statistics."""
    tracker = PomodoroTracker(str(tmp_path / "sessions.json"))
    tracker.start_focus_session(duration_minutes=25)
    tracker.start_focus_session(duration_minutes=25)
    tracker.start_focus_session(duration_minutes=50)

    stats = tracker.get_stats(days=1)
    assert stats["total_focus_sessions"] == 3
    assert stats["total_focus_minutes"] == 100


def test_get_today_sessions(tmp_path):
    """Test getting today's sessions."""
    tracker = PomodoroTracker(str(tmp_path / "sessions.json"))
    tracker.start_focus_session()
    tracker.start_focus_session()

    today_sessions = tracker.get_today_sessions()
    assert len(today_sessions) == 2


def test_streak(tmp_path):
    """Test streak calculation."""
    tracker = PomodoroTracker(str(tmp_path / "sessions.json"))
    tracker.start_focus_session()

    streak = tracker.get_current_streak()
    assert streak >= 1
