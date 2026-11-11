"""
CLI interface for pomodoro-timer.
"""

import click
from rich.console import Console
from rich.panel import Panel
from rich.progress import BarColumn, Progress, TimeRemainingColumn
from rich.table import Table

from . import __version__
from .timer import countdown_timer
from .tracker import (
    DEFAULT_FOCUS_MINUTES,
    LONG_BREAK_MINUTES,
    POMODOROS_PER_CYCLE,
    SHORT_BREAK_MINUTES,
    PomodoroTracker,
)

console = Console()


def _run_countdown(total_seconds: int, description: str) -> None:
    """Show a progress bar while ``countdown_timer`` runs."""
    with Progress(
        "[progress.description]{task.description}",
        BarColumn(),
        "[progress.percentage]{task.percentage:>3.0f}%",
        TimeRemainingColumn(),
        console=console,
    ) as progress:
        task = progress.add_task(description, total=total_seconds)

        def on_tick(remaining: int) -> None:
            progress.update(task, completed=total_seconds - remaining)

        countdown_timer(total_seconds, on_tick=on_tick)
        progress.update(task, completed=total_seconds)


def _print_next_break(tracker: PomodoroTracker) -> None:
    remaining = tracker.get_sessions_until_long_break()
    if remaining == 0:
        console.print("Next: long break (completed a 4-session cycle).")
        return
    noun = "session" if remaining == 1 else "sessions"
    console.print(f"Next: short break ({remaining} focus {noun} until a long break).")


@click.group()
@click.version_option(version=__version__)
@click.pass_context
def main(ctx):
    """Pomodoro Timer - Boost your productivity with the Pomodoro Technique."""
    ctx.ensure_object(dict)
    ctx.obj["tracker"] = PomodoroTracker()


@main.command()
@click.option(
    "--minutes",
    "-m",
    default=DEFAULT_FOCUS_MINUTES,
    show_default=True,
    type=click.IntRange(min=1),
    help="Focus duration in minutes.",
)
@click.pass_context
def focus(ctx, minutes):
    """Start a focus session."""
    tracker = ctx.obj["tracker"]

    console.print(Panel.fit(
        f"[bold red]Focus Session[/bold red]\n\nDuration: {minutes} minutes\n\n"
        "Stay focused and avoid distractions!",
        border_style="red",
    ))

    _run_countdown(minutes * 60, "Focusing...")

    session = tracker.start_focus_session(duration_minutes=minutes)

    console.print(f"\n✅ Focus session complete! Session #{session.id}")
    console.print(f"⏱️  Duration: {minutes} minutes")
    console.print("🔥 Nice work! Take a break!")
    _print_next_break(tracker)


# Named explicitly so Click 8.0 and 8.1 do not expose this as "break-cmd".
@main.command(name="break")
@click.option(
    "--type",
    "break_type",
    default=None,
    type=click.Choice(["short", "long"]),
    help="Break length: short (5 minutes) or long (15 minutes). Defaults to short.",
)
@click.option(
    "--auto",
    is_flag=True,
    help="Long break after every 4th focus session today; otherwise a short break.",
)
@click.pass_context
def break_cmd(ctx, break_type, auto):
    """Take a break."""
    if auto and break_type is not None:
        raise click.UsageError("Use either --auto or --type, not both.")

    tracker = ctx.obj["tracker"]
    if auto:
        break_type = tracker.get_recommended_break()
    elif break_type is None:
        break_type = "short"

    duration = LONG_BREAK_MINUTES if break_type == "long" else SHORT_BREAK_MINUTES

    console.print(Panel.fit(
        f"[bold blue]{break_type.title()} Break[/bold blue]\n\nDuration: {duration} minutes\n\n"
        "Relax and recharge!",
        border_style="blue",
    ))

    _run_countdown(duration * 60, "On break...")
    tracker.start_break(break_type=break_type, duration_minutes=duration)

    console.print("\n✅ Break over! Ready to focus again?")


@main.command()
@click.option(
    "--days",
    "-d",
    default=7,
    show_default=True,
    type=click.IntRange(min=1),
    help="Number of days to show stats for.",
)
@click.pass_context
def stats(ctx, days):
    """Show productivity statistics."""
    tracker = ctx.obj["tracker"]
    summary = tracker.get_stats(days=days)
    streak = tracker.get_current_streak()
    remaining = tracker.get_sessions_until_long_break()
    if remaining == 0:
        done = POMODOROS_PER_CYCLE
        next_break = "long"
    else:
        done = POMODOROS_PER_CYCLE - remaining
        next_break = "short"

    console.print(Panel.fit(
        f"[bold cyan]Pomodoro Statistics[/bold cyan]\n\n"
        f"Period: Last {days} days\n\n"
        f"Total Focus Sessions: {summary['total_focus_sessions']}\n"
        f"Total Focus Time: {summary['total_focus_minutes']} minutes\n"
        f"Average per Day: {summary['average_per_day']} sessions\n"
        f"🔥 Current Streak: {streak} days\n"
        f"Cycle: {done}/{POMODOROS_PER_CYCLE}\n"
        f"Next break: {next_break}",
        border_style="cyan",
    ))

    if summary["daily"]:
        console.print("\n📅 Daily Breakdown:")
        table = Table(show_header=True)
        table.add_column("Date", style="cyan")
        table.add_column("Sessions", style="green")
        table.add_column("Minutes", style="yellow")

        for day, data in sorted(summary["daily"].items()):
            table.add_row(day, str(data["count"]), str(data["minutes"]))

        console.print(table)


if __name__ == "__main__":
    main()
