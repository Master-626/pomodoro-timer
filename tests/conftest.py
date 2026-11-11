"""Keep tests from writing session history into the real home directory."""

import pytest


@pytest.fixture(autouse=True)
def isolate_home(tmp_path, monkeypatch):
    monkeypatch.setattr("pomodoro_timer.tracker.Path.home", lambda: tmp_path)
    return tmp_path
