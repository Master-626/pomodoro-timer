# Pomodoro Timer

## 概述

`pomodoro-timer` 是一个本地使用的命令行番茄钟。用 `pomodoro focus` 开始专注，用 `pomodoro break` 休息，完成的记录保存在 `~/.pomodoro-timer/sessions.json`。`pomodoro stats` 查看最近几天的专注次数、总时长和连续打卡。每完成 4 次专注，`pomodoro break --auto` 会改成长休息。

[![CI](https://github.com/Master-626/pomodoro-timer/actions/workflows/ci.yml/badge.svg)](https://github.com/Master-626/pomodoro-timer/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/)
[![Productivity Tool](https://img.shields.io/badge/productivity-tool-green.svg)]()

A local command-line Pomodoro timer. It records every finished focus session and break, then reports focus time, a daily streak, and where you are in the 4-session cycle.

## Features

- **Focus timer** — 25 minutes by default, or any positive number of minutes
- **Break timer** — 5-minute short breaks and 15-minute long breaks
- **Cycle hint** — after every 4th focus session, the next break should be long
- **Statistics** — session count, total minutes, and the daily average over a window you choose
- **Streak** — consecutive days, ending today, with at least one focus session
- **Daily breakdown** — one row per day inside the requested window
- **Local history** — sessions are stored in a JSON file on your machine
- **Python API** — the same tracker the CLI uses

`pomo` is an alias for `pomodoro`. A session is written only after the timer finishes. Press Ctrl+C to stop early; that attempt is not recorded.

## Installation

Python 3.8 or newer.

```bash
git clone https://github.com/Master-626/pomodoro-timer.git
cd pomodoro-timer
python -m pip install .
```

To work on the code, tests, and lint:

```bash
python -m pip install -e ".[dev]"
```

## Usage

Start a 25-minute focus session:

```bash
pomodoro focus
```

Start a 50-minute focus session:

```bash
pomodoro focus --minutes 50
```

Take a 5-minute break, then a 15-minute break:

```bash
pomodoro break
pomodoro break --type long
```

Let today's cycle choose the break. This is a long break when you have just finished 4, 8, 12, … focus sessions since the last long break, and a short break otherwise:

```bash
pomodoro break --auto
```

Show the last 7 days, or the last 30:

```bash
pomodoro stats
pomodoro stats --days 30
```

`stats` prints the totals, the current streak, cycle progress such as `Cycle: 2/4`, and a daily table. The daily table includes every day in the window that has a focus session.

## Options

| Command | Option | Default | Meaning |
| --- | --- | --- | --- |
| `focus` | `-m`, `--minutes` | `25` | Focus length in minutes. Integer, at least 1. |
| `break` | `--type` | `short` | `short` is 5 minutes, `long` is 15 minutes. |
| `break` | `--auto` | off | Choose `short` or `long` from today's 4-session cycle. Do not combine with `--type`. |
| `stats` | `-d`, `--days` | `7` | Inclusive window ending today. Integer, at least 1. |

`--version` prints the installed version. `--help` on the program or on any command lists the same options.

## Where sessions are stored

The CLI writes `~/.pomodoro-timer/sessions.json`. Each record has an id, a type (`focus`, `short_break`, or `long_break`), a duration in minutes, a completion timestamp, and a date. The file is replaced atomically. Creating a `PomodoroTracker` with an explicit path stores history there instead.

The streak counts backward from today and stops at the first day without a focus session. Before today's first finished focus session it is 0. Breaks do not count as focus time and do not increase the streak. A short break also does not reset the 4-session cycle; a long break does.

`average_per_day` is focus sessions divided by the whole window, including days you did not work.

## The Pomodoro Technique

1. Choose a task.
2. Focus until the timer ends (traditionally 25 minutes).
3. Take a short break (5 minutes).
4. After four focus sessions, take a long break (15 minutes) instead.
5. Repeat.

## Python API

```python
from pomodoro_timer.tracker import PomodoroTracker

tracker = PomodoroTracker()  # or PomodoroTracker("/tmp/sessions.json")

session = tracker.start_focus_session(duration_minutes=25)
print(session.id, session.type)

tracker.start_break(break_type="short", duration_minutes=5)

stats = tracker.get_stats(days=7)
print(stats["total_focus_minutes"], stats["average_per_day"])

print(tracker.get_current_streak())
print(tracker.get_cycle_focus_count(), tracker.get_recommended_break())
```

`start_break("short")` stores `short_break`, and `start_break("long")` stores `long_break`. Durations and the `days` argument must be positive integers. An empty history file loads as no sessions. Malformed JSON raises `ValueError`.

`countdown_timer` and `format_time` live in `pomodoro_timer.timer`. `format_time` returns `MM:SS` (hours roll into the minute field, so 3600 seconds is `60:00`).

## Running tests

```bash
python -m pip install -e ".[dev]"
python -m ruff check .
python -m pytest
```

GitHub Actions runs those two commands on Python 3.8, 3.9, 3.10, 3.11, 3.12, and 3.13.

## License

MIT License
