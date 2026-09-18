# Pomodoro Timer

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/)
[![Productivity Tool](https://img.shields.io/badge/productivity-tool-green.svg)]()

A Pomodoro technique timer with productivity tracking and statistics. Boost your focus and get more done!

## 🌟 Features

- ⏱️ **Focus Timer** - 25-minute focus sessions (customizable)
- ☕ **Break Timer** - Short (5min) and long (15min) breaks
- 📊 **Statistics** - Track your productivity over time
- 🔥 **Streak Tracking** - Build a daily habit streak
- 📅 **Daily Breakdown** - See your daily focus sessions
- 🎨 **Rich Output** - Beautiful terminal progress bars and stats
- 💾 **Persistent** - Sessions saved locally
- 🐍 **Python API** - Use as a library in your code

## 📦 Installation

```bash
git clone https://github.com/Master-626/pomodoro-timer.git
cd pomodoro-timer
pip install .
```

## 🚀 Usage

### Start Focus Session
```bash
# Default 25-minute focus
pomodoro focus

# Custom duration (e.g. 50 minutes)
pomodoro focus --minutes 50
```

### Take a Break
```bash
# Short break (5 minutes)
pomodoro break

# Long break (15 minutes)
pomodoro break --type long
```

### View Statistics
```bash
# Last 7 days stats (default)
pomodoro stats

# Last 30 days
pomodoro stats --days 30
```

## 🍅 The Pomodoro Technique

1. **Choose a task** you want to work on
2. **Set the timer** for 25 minutes
3. **Work on the task** until the timer rings
4. **Take a short break** (5 minutes)
5. **Repeat** 4 times, then take a long break (15-30 minutes)

## 🐍 Python API

```python
from pomodoro_timer.tracker import PomodoroTracker

tracker = PomodoroTracker()

# Record a focus session
session = tracker.start_focus_session(duration_minutes=25)

# Get statistics
stats = tracker.get_stats(days=7)
print(f"Total focus time: {stats['total_focus_minutes']} minutes")

# Get current streak
streak = tracker.get_current_streak()
print(f"Current streak: {streak} days")
```

## 🧪 Testing

```bash
pip install -e ".[dev]"
pytest
```

## 📄 License

MIT License
