"""
Pomodoro timer logic and tracking.
"""

import json
from dataclasses import dataclass, asdict
from datetime import datetime, date
from pathlib import Path
from typing import List, Optional
from enum import Enum


class SessionType(Enum):
    FOCUS = "focus"
    SHORT_BREAK = "short_break"
    LONG_BREAK = "long_break"


@dataclass
class Session:
    id: int
    type: str
    duration_minutes: int
    completed_at: str
    date: str


class PomodoroTracker:
    """Track pomodoro sessions and statistics."""

    def __init__(self, file_path: str = None):
        if file_path is None:
            home = Path.home()
            data_dir = home / ".pomodoro-timer"
            data_dir.mkdir(exist_ok=True)
            file_path = str(data_dir / "sessions.json")
        self.file_path = Path(file_path)
        self.sessions: List[Session] = []
        self._load()

    def _load(self):
        """Load sessions from file."""
        if self.file_path.exists():
            data = json.loads(self.file_path.read_text(encoding="utf-8"))
            self.sessions = [Session(**s) for s in data]

    def _save(self):
        """Save sessions to file."""
        data = [asdict(s) for s in self.sessions]
        self.file_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def start_focus_session(self, duration_minutes: int = 25) -> Session:
        """Record a completed focus session."""
        session_id = max((s.id for s in self.sessions), default=0) + 1
        today = date.today().isoformat()
        now = datetime.now().isoformat()

        session = Session(
            id=session_id,
            type=SessionType.FOCUS.value,
            duration_minutes=duration_minutes,
            completed_at=now,
            date=today,
        )
        self.sessions.append(session)
        self._save()
        return session

    def start_break(self, break_type: str = "short", duration_minutes: int = 5) -> Session:
        """Record a break session."""
        session_id = max((s.id for s in self.sessions), default=0) + 1
        today = date.today().isoformat()
        now = datetime.now().isoformat()

        session = Session(
            id=session_id,
            type=break_type,
            duration_minutes=duration_minutes,
            completed_at=now,
            date=today,
        )
        self.sessions.append(session)
        self._save()
        return session

    def get_today_sessions(self) -> List[Session]:
        """Get today's sessions."""
        today = date.today().isoformat()
        return [s for s in self.sessions if s.date == today]

    def get_stats(self, days: int = 7) -> dict:
        """Get statistics for the last N days."""
        from datetime import timedelta

        end_date = date.today()
        start_date = end_date - timedelta(days=days - 1)

        filtered = [
            s for s in self.sessions
            if start_date.isoformat() <= s.date <= end_date.isoformat()
        ]

        focus_sessions = [s for s in filtered if s.type == SessionType.FOCUS.value]
        total_focus_minutes = sum(s.duration_minutes for s in focus_sessions)

        # Per day breakdown
        daily = {}
        for s in focus_sessions:
            if s.date not in daily:
                daily[s.date] = {"count": 0, "minutes": 0}
            daily[s.date]["count"] += 1
            daily[s.date]["minutes"] += s.duration_minutes

        return {
            "total_focus_sessions": len(focus_sessions),
            "total_focus_minutes": total_focus_minutes,
            "average_per_day": round(len(focus_sessions) / days, 1) if days > 0 else 0,
            "daily": daily,
        }

    def get_current_streak(self) -> int:
        """Get current streak of days with at least one focus session."""
        if not self.sessions:
            return 0

        focus_dates = sorted(set(s.date for s in self.sessions if s.type == SessionType.FOCUS.value))

        streak = 0
        current = date.today()

        for i in range(len(focus_dates) - 1, -1, -1):
            session_date = date.fromisoformat(focus_dates[i])
            diff = (current - session_date).days
            if diff == streak:
                streak += 1
                current = session_date
            elif diff > streak:
                break

        return streak
