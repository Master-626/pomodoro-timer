"""
Pomodoro timer logic and tracking.
"""

import json
from dataclasses import asdict, dataclass
from datetime import date, datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional


class SessionType(Enum):
    FOCUS = "focus"
    SHORT_BREAK = "short_break"
    LONG_BREAK = "long_break"


# Classic Pomodoro lengths. A long break follows every 4th focus session.
DEFAULT_FOCUS_MINUTES = 25
SHORT_BREAK_MINUTES = 5
LONG_BREAK_MINUTES = 15
POMODOROS_PER_CYCLE = 4

_BREAK_TYPES = {
    "short": SessionType.SHORT_BREAK.value,
    "short_break": SessionType.SHORT_BREAK.value,
    "long": SessionType.LONG_BREAK.value,
    "long_break": SessionType.LONG_BREAK.value,
}

_SESSION_FIELDS = ("id", "type", "duration_minutes", "completed_at", "date")


@dataclass
class Session:
    id: int
    type: str
    duration_minutes: int
    completed_at: str
    date: str


class PomodoroTracker:
    """Track pomodoro sessions and statistics."""

    def __init__(self, file_path: Optional[str] = None):
        if file_path is None:
            data_dir = Path.home() / ".pomodoro-timer"
            data_dir.mkdir(exist_ok=True)
            file_path = str(data_dir / "sessions.json")
        self.file_path = Path(file_path)
        self.sessions: List[Session] = []
        self._load()

    def _load(self):
        """Load sessions from file."""
        if not self.file_path.exists():
            return
        raw = self.file_path.read_text(encoding="utf-8")
        if not raw.strip():
            self.sessions = []
            return
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Could not read sessions from {self.file_path}") from exc
        if not isinstance(data, list):
            raise ValueError(f"Sessions file must contain a list: {self.file_path}")

        sessions = []
        for record in data:
            sessions.append(self._session_from_record(record))
        self.sessions = sessions

    def _session_from_record(self, record) -> Session:
        if not isinstance(record, dict) or any(field not in record for field in _SESSION_FIELDS):
            raise ValueError(f"Invalid session record in {self.file_path}")
        payload = {field: record[field] for field in _SESSION_FIELDS}
        session_type = payload.get("type")
        if session_type in _BREAK_TYPES:
            payload["type"] = _BREAK_TYPES[session_type]
        return Session(**payload)

    def _save(self):
        """Save sessions to file."""
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        data = [asdict(session) for session in self.sessions]
        payload = json.dumps(data, indent=2)
        # Write aside and replace so a crash cannot truncate the history.
        temporary = self.file_path.with_name(self.file_path.name + ".tmp")
        temporary.write_text(payload, encoding="utf-8")
        temporary.replace(self.file_path)

    def _validate_duration(self, duration_minutes: int) -> None:
        if isinstance(duration_minutes, bool) or not isinstance(duration_minutes, int):
            raise TypeError("duration_minutes must be a positive integer")
        if duration_minutes < 1:
            raise ValueError("duration_minutes must be a positive integer")

    def _add_session(self, session_type: str, duration_minutes: int) -> Session:
        self._validate_duration(duration_minutes)
        session_id = max((session.id for session in self.sessions), default=0) + 1
        today = date.today().isoformat()
        session = Session(
            id=session_id,
            type=session_type,
            duration_minutes=duration_minutes,
            completed_at=datetime.now().isoformat(),
            date=today,
        )
        self.sessions.append(session)
        self._save()
        return session

    def start_focus_session(self, duration_minutes: int = DEFAULT_FOCUS_MINUTES) -> Session:
        """Record a completed focus session."""
        return self._add_session(SessionType.FOCUS.value, duration_minutes)

    def start_break(
        self,
        break_type: str = "short",
        duration_minutes: int = SHORT_BREAK_MINUTES,
    ) -> Session:
        """Record a break session.

        ``break_type`` is ``short`` or ``long``. The stored type is the
        canonical ``short_break`` or ``long_break`` value.
        """
        canonical = _BREAK_TYPES.get(break_type)
        if canonical is None:
            raise ValueError("break_type must be 'short' or 'long'")
        return self._add_session(canonical, duration_minutes)

    def get_today_sessions(self) -> List[Session]:
        """Get today's sessions."""
        today = date.today().isoformat()
        return [session for session in self.sessions if session.date == today]

    def get_stats(self, days: int = 7) -> dict:
        """Get statistics for the last N days, including today.

        ``average_per_day`` divides focus sessions by the size of the window,
        so days with no sessions count as zero.
        """
        if isinstance(days, bool) or not isinstance(days, int) or days < 1:
            raise ValueError("days must be a positive integer")

        end_date = date.today()
        start_date = end_date - timedelta(days=days - 1)

        filtered = [
            session
            for session in self.sessions
            if start_date.isoformat() <= session.date <= end_date.isoformat()
        ]

        focus_sessions = [
            session for session in filtered if session.type == SessionType.FOCUS.value
        ]
        total_focus_minutes = sum(session.duration_minutes for session in focus_sessions)

        daily: Dict[str, Dict[str, int]] = {}
        for session in focus_sessions:
            if session.date not in daily:
                daily[session.date] = {"count": 0, "minutes": 0}
            daily[session.date]["count"] += 1
            daily[session.date]["minutes"] += session.duration_minutes

        return {
            "total_focus_sessions": len(focus_sessions),
            "total_focus_minutes": total_focus_minutes,
            "average_per_day": round(len(focus_sessions) / days, 1),
            "daily": daily,
        }

    def get_current_streak(self) -> int:
        """Return consecutive focus days ending today.

        Each day counts at most once. The streak is 0 when today has no
        focus session, even if yesterday did.
        """
        focus_days = {
            date.fromisoformat(session.date)
            for session in self.sessions
            if session.type == SessionType.FOCUS.value
        }
        cursor = date.today()
        streak = 0
        while cursor in focus_days:
            streak += 1
            cursor -= timedelta(days=1)
        return streak

    def get_cycle_focus_count(self, day: Optional[date] = None) -> int:
        """Focus sessions on ``day`` since the last long break that day.

        Short breaks do not reset the cycle. Sessions from other days are
        ignored, and order follows ``completed_at`` rather than file order.
        """
        target = date.today() if day is None else day
        iso = target.isoformat()
        todays = sorted(
            (session for session in self.sessions if session.date == iso),
            key=lambda session: (session.completed_at, session.id),
        )
        count = 0
        for session in todays:
            if session.type == SessionType.LONG_BREAK.value:
                count = 0
            elif session.type == SessionType.FOCUS.value:
                count += 1
        return count

    def get_sessions_until_long_break(self, day: Optional[date] = None) -> int:
        """How many more focus sessions are due before the next long break.

        Returns 0 when a long break is due now (the count is a positive
        multiple of 4). Returns 4 when the cycle has not started.
        """
        count = self.get_cycle_focus_count(day)
        if count > 0 and count % POMODOROS_PER_CYCLE == 0:
            return 0
        return POMODOROS_PER_CYCLE - (count % POMODOROS_PER_CYCLE)

    def get_recommended_break(self, day: Optional[date] = None) -> str:
        """Return ``long`` after every 4th focus session, otherwise ``short``."""
        if self.get_sessions_until_long_break(day) == 0:
            return "long"
        return "short"
