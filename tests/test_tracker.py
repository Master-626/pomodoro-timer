import json
from datetime import date, timedelta

import pytest

from pomodoro_timer.tracker import PomodoroTracker, Session


def _focus(day, session_id, at="12:00:00"):
    return Session(
        id=session_id,
        type="focus",
        duration_minutes=25,
        completed_at=f"{day.isoformat()}T{at}",
        date=day.isoformat(),
    )


def test_start_focus_session(tmp_path):
    """Test starting a focus session."""
    tracker = PomodoroTracker(str(tmp_path / "sessions.json"))
    session = tracker.start_focus_session(duration_minutes=25)
    assert session.type == "focus"
    assert session.duration_minutes == 25
    assert session.id == 1
    assert len(tracker.sessions) == 1


def test_start_break(tmp_path):
    """Test starting a break."""
    tracker = PomodoroTracker(str(tmp_path / "sessions.json"))
    session = tracker.start_break(break_type="short", duration_minutes=5)
    assert session.type == "short_break"
    assert session.duration_minutes == 5


def test_start_long_break_and_canonical_alias(tmp_path):
    tracker = PomodoroTracker(str(tmp_path / "sessions.json"))
    long_break = tracker.start_break("long", 15)
    alias = tracker.start_break("short_break", 5)
    assert long_break.type == "long_break"
    assert alias.type == "short_break"
    assert [session.id for session in tracker.sessions] == [1, 2]


def test_invalid_break_type_is_rejected(tmp_path):
    path = tmp_path / "sessions.json"
    tracker = PomodoroTracker(str(path))
    with pytest.raises(ValueError):
        tracker.start_break("nap", 5)
    assert tracker.sessions == []
    assert not path.exists()


def test_get_stats(tmp_path):
    """Test getting statistics."""
    tracker = PomodoroTracker(str(tmp_path / "sessions.json"))
    tracker.start_focus_session(duration_minutes=25)
    tracker.start_focus_session(duration_minutes=25)
    tracker.start_focus_session(duration_minutes=50)

    stats = tracker.get_stats(days=1)
    assert stats["total_focus_sessions"] == 3
    assert stats["total_focus_minutes"] == 100
    assert stats["average_per_day"] == 3.0


def test_get_stats_ignores_breaks_and_days_outside_the_window(tmp_path):
    today = date.today()
    tracker = PomodoroTracker(str(tmp_path / "sessions.json"))
    tracker.sessions = [
        _focus(today, 1),
        _focus(today - timedelta(days=6), 2),
        _focus(today - timedelta(days=7), 3),
        Session(4, "short_break", 5, f"{today.isoformat()}T13:00:00", today.isoformat()),
    ]

    stats = tracker.get_stats(days=7)
    assert stats["total_focus_sessions"] == 2
    assert stats["total_focus_minutes"] == 50
    assert stats["average_per_day"] == round(2 / 7, 1)
    assert today.isoformat() in stats["daily"]
    assert (today - timedelta(days=6)).isoformat() in stats["daily"]
    assert (today - timedelta(days=7)).isoformat() not in stats["daily"]


def test_get_stats_rejects_non_positive_days(tmp_path):
    tracker = PomodoroTracker(str(tmp_path / "sessions.json"))
    with pytest.raises(ValueError):
        tracker.get_stats(0)
    with pytest.raises(ValueError):
        tracker.get_stats(-3)
    with pytest.raises(ValueError):
        tracker.get_stats(True)


def test_get_today_sessions(tmp_path):
    """Test getting today's sessions."""
    tracker = PomodoroTracker(str(tmp_path / "sessions.json"))
    tracker.start_focus_session()
    tracker.start_focus_session()
    tracker.start_break("short", 5)

    today_sessions = tracker.get_today_sessions()
    assert len(today_sessions) == 3
    assert [session.type for session in today_sessions].count("focus") == 2


def test_streak(tmp_path):
    """Test streak calculation."""
    tracker = PomodoroTracker(str(tmp_path / "sessions.json"))
    tracker.start_focus_session()

    streak = tracker.get_current_streak()
    assert streak == 1


def test_streak_counts_consecutive_days_and_stops_at_a_gap(tmp_path):
    today = date.today()
    tracker = PomodoroTracker(str(tmp_path / "sessions.json"))
    tracker.sessions = [
        _focus(today - timedelta(days=offset), offset + 1) for offset in range(9, -1, -1)
    ]
    assert tracker.get_current_streak() == 10

    tracker.sessions = [
        _focus(today - timedelta(days=3), 1),
        _focus(today - timedelta(days=1), 2),
        _focus(today, 3),
    ]
    assert tracker.get_current_streak() == 2

    tracker.sessions = [_focus(today - timedelta(days=2), 1), _focus(today, 2)]
    assert tracker.get_current_streak() == 1

    tracker.sessions = [_focus(today - timedelta(days=1), 1)]
    assert tracker.get_current_streak() == 0

    tracker.sessions = [
        Session(1, "short_break", 5, f"{today.isoformat()}T12:00:00", today.isoformat())
    ]
    assert tracker.get_current_streak() == 0


def test_empty_tracker_stats_and_streak(tmp_path):
    tracker = PomodoroTracker(str(tmp_path / "sessions.json"))
    stats = tracker.get_stats()
    assert stats["total_focus_sessions"] == 0
    assert stats["total_focus_minutes"] == 0
    assert stats["average_per_day"] == 0.0
    assert stats["daily"] == {}
    assert tracker.get_current_streak() == 0
    assert tracker.get_today_sessions() == []


def test_sessions_reload_and_ids_keep_growing(tmp_path):
    path = tmp_path / "sessions.json"
    tracker = PomodoroTracker(str(path))
    tracker.start_focus_session(25)
    tracker.start_break("short", 5)

    reloaded = PomodoroTracker(str(path))
    assert [(session.type, session.duration_minutes) for session in reloaded.sessions] == [
        ("focus", 25),
        ("short_break", 5),
    ]
    assert reloaded.start_focus_session(50).id == 3
    assert not path.with_name(path.name + ".tmp").exists()


def test_custom_directory_is_created(tmp_path):
    path = tmp_path / "nested" / "dir" / "sessions.json"
    tracker = PomodoroTracker(str(path))
    tracker.start_focus_session(25)
    assert path.is_file()
    assert len(PomodoroTracker(str(path)).sessions) == 1


def test_default_path_is_under_home(tmp_path):
    tracker = PomodoroTracker()
    assert tracker.file_path == tmp_path / ".pomodoro-timer" / "sessions.json"
    assert tracker.file_path.parent.is_dir()


def test_empty_file_loads_as_no_history(tmp_path):
    path = tmp_path / "sessions.json"
    path.write_text("\n\n", encoding="utf-8")
    tracker = PomodoroTracker(str(path))
    assert tracker.sessions == []


def test_malformed_sessions_file_raises(tmp_path):
    path = tmp_path / "sessions.json"
    path.write_text("{", encoding="utf-8")
    with pytest.raises(ValueError):
        PomodoroTracker(str(path))

    path.write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError):
        PomodoroTracker(str(path))

    path.write_text(json.dumps([{"id": 1}]), encoding="utf-8")
    with pytest.raises(ValueError):
        PomodoroTracker(str(path))


def test_legacy_break_names_load_without_rewriting_until_save(tmp_path):
    today = date.today().isoformat()
    path = tmp_path / "sessions.json"
    original = json.dumps(
        [
            {
                "id": 1,
                "type": "short",
                "duration_minutes": 5,
                "completed_at": f"{today}T12:00:00",
                "date": today,
                "note": "ignored extra field",
            }
        ]
    )
    path.write_text(original, encoding="utf-8")

    tracker = PomodoroTracker(str(path))
    assert tracker.sessions[0].type == "short_break"
    assert path.read_text(encoding="utf-8") == original

    tracker.start_focus_session(25)
    saved = json.loads(path.read_text(encoding="utf-8"))
    assert saved[0]["type"] == "short_break"
    assert "note" not in saved[0]


def test_legacy_zero_duration_record_still_loads(tmp_path):
    today = date.today().isoformat()
    path = tmp_path / "sessions.json"
    path.write_text(
        json.dumps(
            [
                {
                    "id": 1,
                    "type": "focus",
                    "duration_minutes": 0,
                    "completed_at": f"{today}T12:00:00",
                    "date": today,
                }
            ]
        ),
        encoding="utf-8",
    )
    tracker = PomodoroTracker(str(path))
    assert tracker.sessions[0].duration_minutes == 0


def test_non_positive_duration_is_rejected(tmp_path):
    path = tmp_path / "sessions.json"
    tracker = PomodoroTracker(str(path))
    with pytest.raises(ValueError):
        tracker.start_focus_session(0)
    with pytest.raises(ValueError):
        tracker.start_break("long", -15)
    with pytest.raises(TypeError):
        tracker.start_focus_session(True)
    with pytest.raises(TypeError):
        tracker.start_focus_session(25.5)
    assert tracker.sessions == []
    assert not path.exists()


@pytest.mark.parametrize(
    ("focuses", "long_break_after", "expected_count", "expected_remaining", "expected_break"),
    [
        (0, False, 0, 4, "short"),
        (1, False, 1, 3, "short"),
        (3, False, 3, 1, "short"),
        (4, False, 4, 0, "long"),
        (5, False, 5, 3, "short"),
        (8, False, 8, 0, "long"),
        (4, True, 0, 4, "short"),
    ],
)
def test_recommended_break_follows_four_session_cycle(
    tmp_path, focuses, long_break_after, expected_count, expected_remaining, expected_break
):
    tracker = PomodoroTracker(str(tmp_path / "sessions.json"))
    for _ in range(focuses):
        tracker.start_focus_session(25)
    if long_break_after:
        tracker.start_break("long", 15)

    assert tracker.get_cycle_focus_count() == expected_count
    assert tracker.get_sessions_until_long_break() == expected_remaining
    assert tracker.get_recommended_break() == expected_break


def test_legacy_long_break_name_resets_the_cycle(tmp_path):
    today = date.today().isoformat()
    path = tmp_path / "sessions.json"
    path.write_text(
        json.dumps(
            [
                {
                    "id": index,
                    "type": "focus",
                    "duration_minutes": 25,
                    "completed_at": f"{today}T09:0{index}:00",
                    "date": today,
                }
                for index in range(1, 5)
            ]
            + [
                {
                    "id": 5,
                    "type": "long",
                    "duration_minutes": 15,
                    "completed_at": f"{today}T13:00:00",
                    "date": today,
                }
            ]
        ),
        encoding="utf-8",
    )
    tracker = PomodoroTracker(str(path))
    assert tracker.sessions[-1].type == "long_break"
    assert tracker.get_cycle_focus_count() == 0
    assert tracker.get_recommended_break() == "short"


def test_short_break_does_not_reset_the_cycle(tmp_path):
    tracker = PomodoroTracker(str(tmp_path / "sessions.json"))
    for _ in range(4):
        tracker.start_focus_session(25)
    tracker.start_break("short", 5)
    assert tracker.get_cycle_focus_count() == 4
    assert tracker.get_recommended_break() == "long"


def test_cycle_uses_completion_time_and_ignores_other_days(tmp_path):
    today = date.today()
    yesterday = today - timedelta(days=1)
    tracker = PomodoroTracker(str(tmp_path / "sessions.json"))
    tracker.sessions = [
        Session(1, "long_break", 15, f"{today.isoformat()}T18:00:00", today.isoformat()),
        _focus(today, 2, at="09:00:00"),
        _focus(yesterday, 3, at="09:00:00"),
        _focus(yesterday, 4, at="10:00:00"),
        _focus(yesterday, 5, at="11:00:00"),
        _focus(yesterday, 6, at="12:00:00"),
    ]
    # The long break is listed first but happened after today's focus.
    assert tracker.get_cycle_focus_count() == 0
    assert tracker.get_recommended_break() == "short"
    assert tracker.get_cycle_focus_count(yesterday) == 4
    assert tracker.get_recommended_break(yesterday) == "long"
