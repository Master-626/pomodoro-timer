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
    """Run a countdown timer."""
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
    """Format seconds into MM:SS format."""
    minutes = seconds // 60
    secs = seconds % 60
    return f"{minutes:02d}:{secs:02d}"
