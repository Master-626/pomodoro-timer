import pytest

from pomodoro_timer.timer import countdown_timer, format_time


@pytest.mark.parametrize(
    ("seconds", "expected"),
    [
        (0, "00:00"),
        (5, "00:05"),
        (61, "01:01"),
        (125, "02:05"),
        (3599, "59:59"),
        (3600, "60:00"),
        (-1, "-00:01"),
        (-60, "-01:00"),
        (-61, "-01:01"),
    ],
)
def test_format_time(seconds, expected):
    assert format_time(seconds) == expected


def test_countdown_ticks_then_completes(monkeypatch):
    sleeps = []
    monkeypatch.setattr("pomodoro_timer.timer.time.sleep", lambda seconds: sleeps.append(seconds))
    ticks = []
    done = []

    assert countdown_timer(3, on_tick=ticks.append, on_complete=lambda: done.append(True)) is True
    assert ticks == [3, 2, 1]
    assert sleeps == [1, 1, 1]
    assert done == [True]


def test_countdown_zero_completes_without_ticking():
    ticks = []
    done = []
    assert countdown_timer(0, on_tick=ticks.append, on_complete=lambda: done.append(True)) is True
    assert ticks == []
    assert done == [True]


def test_negative_countdown_does_not_sleep(monkeypatch):
    def fail(_seconds):
        raise AssertionError("slept")

    monkeypatch.setattr("pomodoro_timer.timer.time.sleep", fail)
    with pytest.raises(ValueError):
        countdown_timer(-1)
