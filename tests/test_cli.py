import json
from datetime import date, timedelta

from click.testing import CliRunner

from pomodoro_timer import __version__
from pomodoro_timer.cli import main
from pomodoro_timer.tracker import PomodoroTracker


def _runner_with_instant_timer(monkeypatch):
    """Invoke commands without waiting, and fail if a real sleep sneaks back in."""
    requested = []

    def instant(seconds, on_tick=None, on_complete=None):
        requested.append(seconds)
        if on_complete:
            on_complete()
        return True

    def fail(_seconds):
        raise AssertionError("timer slept")

    monkeypatch.setattr("pomodoro_timer.cli.countdown_timer", instant)
    monkeypatch.setattr("pomodoro_timer.timer.time.sleep", fail)
    return CliRunner(), requested


def _history(tmp_path):
    return tmp_path / ".pomodoro-timer" / "sessions.json"


def test_commands_are_focus_break_and_stats():
    assert set(main.commands) == {"focus", "break", "stats"}


def test_help_lists_options():
    runner = CliRunner()
    focus_help = runner.invoke(main, ["focus", "--help"])
    break_help = runner.invoke(main, ["break", "--help"])
    stats_help = runner.invoke(main, ["stats", "--help"])
    assert focus_help.exit_code == 0
    assert "--minutes" in focus_help.output
    assert "25" in focus_help.output
    assert break_help.exit_code == 0
    assert "--type" in break_help.output
    assert "--auto" in break_help.output
    assert stats_help.exit_code == 0
    assert "--days" in stats_help.output


def test_version():
    result = CliRunner().invoke(main, ["--version"])
    assert result.exit_code == 0
    assert __version__ in result.output


def test_focus_records_a_session_without_sleeping(tmp_path, monkeypatch):
    runner, requested = _runner_with_instant_timer(monkeypatch)
    result = runner.invoke(main, ["focus", "--minutes", "1"])
    assert result.exit_code == 0, result.output
    assert requested == [60]
    assert "Session #1" in result.output
    assert "3 focus sessions until a long break" in result.output

    saved = json.loads(_history(tmp_path).read_text(encoding="utf-8"))
    assert saved[0]["type"] == "focus"
    assert saved[0]["duration_minutes"] == 1


def test_focus_default_is_25_minutes(tmp_path, monkeypatch):
    runner, requested = _runner_with_instant_timer(monkeypatch)
    result = runner.invoke(main, ["focus"])
    assert result.exit_code == 0, result.output
    assert requested == [25 * 60]
    saved = json.loads(_history(tmp_path).read_text(encoding="utf-8"))
    assert saved[0]["duration_minutes"] == 25


def test_focus_rejects_non_positive_minutes(tmp_path):
    result = CliRunner().invoke(main, ["focus", "--minutes", "0"])
    assert result.exit_code != 0
    tracker = PomodoroTracker()
    assert tracker.sessions == []


def test_break_types_and_auto_cycle(tmp_path, monkeypatch):
    runner, requested = _runner_with_instant_timer(monkeypatch)

    short = runner.invoke(main, ["break"])
    assert short.exit_code == 0, short.output
    assert requested == [5 * 60]

    long_break = runner.invoke(main, ["break", "--type", "long"])
    assert long_break.exit_code == 0, long_break.output
    assert requested[-1] == 15 * 60

    saved = json.loads(_history(tmp_path).read_text(encoding="utf-8"))
    assert [row["type"] for row in saved] == ["short_break", "long_break"]
    assert [row["duration_minutes"] for row in saved] == [5, 15]


def test_auto_break_is_long_after_four_focus_sessions(tmp_path, monkeypatch):
    data_dir = tmp_path / ".pomodoro-timer"
    data_dir.mkdir()
    today = date.today().isoformat()
    rows = [
        {
            "id": index,
            "type": "focus",
            "duration_minutes": 25,
            "completed_at": f"{today}T09:0{index}:00",
            "date": today,
        }
        for index in range(1, 5)
    ]
    (data_dir / "sessions.json").write_text(json.dumps(rows), encoding="utf-8")

    runner, requested = _runner_with_instant_timer(monkeypatch)
    result = runner.invoke(main, ["break", "--auto"])
    assert result.exit_code == 0, result.output
    assert requested == [15 * 60]
    saved = json.loads(_history(tmp_path).read_text(encoding="utf-8"))
    assert saved[-1]["type"] == "long_break"
    assert saved[-1]["duration_minutes"] == 15


def test_auto_and_type_are_mutually_exclusive():
    result = CliRunner().invoke(main, ["break", "--auto", "--type", "long"])
    assert result.exit_code != 0
    assert "not both" in result.output


def test_fourth_focus_recommends_a_long_break(tmp_path, monkeypatch):
    data_dir = tmp_path / ".pomodoro-timer"
    data_dir.mkdir()
    today = date.today().isoformat()
    rows = [
        {
            "id": index,
            "type": "focus",
            "duration_minutes": 25,
            "completed_at": f"{today}T09:0{index}:00",
            "date": today,
        }
        for index in range(1, 4)
    ]
    (data_dir / "sessions.json").write_text(json.dumps(rows), encoding="utf-8")

    runner, _requested = _runner_with_instant_timer(monkeypatch)
    result = runner.invoke(main, ["focus", "--minutes", "25"])
    assert result.exit_code == 0, result.output
    assert "Next: long break" in result.output


def test_stats_lists_every_day_in_the_requested_window(tmp_path, monkeypatch):
    data_dir = tmp_path / ".pomodoro-timer"
    data_dir.mkdir()
    today = date.today()
    rows = []
    for offset in range(10):
        day = today - timedelta(days=offset)
        rows.append(
            {
                "id": offset + 1,
                "type": "focus",
                "duration_minutes": 25,
                "completed_at": f"{day.isoformat()}T12:00:00",
                "date": day.isoformat(),
            }
        )
    outside = today - timedelta(days=30)
    rows.append(
        {
            "id": 11,
            "type": "focus",
            "duration_minutes": 25,
            "completed_at": f"{outside.isoformat()}T12:00:00",
            "date": outside.isoformat(),
        }
    )
    (data_dir / "sessions.json").write_text(json.dumps(rows), encoding="utf-8")

    runner, _requested = _runner_with_instant_timer(monkeypatch)
    result = runner.invoke(main, ["stats", "--days", "30"])
    assert result.exit_code == 0, result.output
    for offset in range(10):
        assert (today - timedelta(days=offset)).isoformat() in result.output
    assert outside.isoformat() not in result.output
    assert "Total Focus Sessions: 10" in result.output
    assert "Cycle: 1/4" in result.output
    assert "Next break: short" in result.output


def test_stats_with_no_history(monkeypatch):
    runner, _requested = _runner_with_instant_timer(monkeypatch)
    result = runner.invoke(main, ["stats"])
    assert result.exit_code == 0, result.output
    assert "Total Focus Sessions: 0" in result.output
    assert "Current Streak: 0" in result.output
    assert "Cycle: 0/4" in result.output
    assert "Daily Breakdown" not in result.output
