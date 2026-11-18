"""
Timer utilities.
"""

import time
from typing import Callable, Optional


def countdown_timer(
    seconds: int,
    on_tick: Optional[Callable[[int], None]] = None,
    on_complete: Optional[Callable[[], None]] = None,
):
    """Run a countdown timer.

    ``on_tick`` receives the remaining seconds before each one-second wait,
    from ``seconds`` down to 1. A zero-length countdown completes immediately.
    """
    if seconds < 0:
        raise ValueError("seconds must be non-negative")

    remaining = seconds
    while remaining > 0:
        if on_tick:
            on_tick(remaining)
        time.sleep(1)
        remaining -= 1

    if on_complete:
        on_complete()

    return True


def format_time(seconds: int) -> str:
    """Format seconds as MM:SS. A negative duration keeps a leading minus."""
    sign = "-" if seconds < 0 else ""
    minutes, secs = divmod(abs(seconds), 60)
    return f"{sign}{minutes:02d}:{secs:02d}"
