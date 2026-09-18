"""
CLI interface for pomodoro-timer.
"""

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, BarColumn, TimeRemainingColumn

from .tracker import PomodoroTracker
from .timer import countdown_timer, format_time

console = Console()


@click.group()
@click.version_option(version="0.1.0")
@click.pass_context
def main(ctx):
    """Pomodoro Timer - Boost your productivity with the Pomodoro Technique."""
    ctx.ensure_object(dict)
    ctx.obj["tracker"] = PomodoroTracker()


@main.command()
@click.option("--minutes", "-m", default=25, help="Focus duration in minutes")
@click.pass_context
def focus(ctx, minutes):
    """Start a focus session."""
    tracker = ctx.obj["tracker"]

    console.print(Panel.fit(
        f"[bold red]Focus Session[/bold red]\n\nDuration: {minutes} minutes\n\n"
        "Stay focused and avoid distractions!",
        border_style="red"
    ))

    total_seconds = minutes * 60

    # Run countdown
    with Progress(
        "[progress.description]{task.description}",
        BarColumn(),
        "[progress.percentage]{task.percentage:>3.0f}%",
        TimeRemainingColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("Focusing...", total=total_seconds)

        for i in range(total_seconds, 0, -1):
            progress.update(task, completed=total_seconds - i)
            time.sleep(1)

    # Record the session
    session = tracker.start_focus_session(duration_minutes=minutes)

    console.print(f"\n✅ Focus session complete! Session #{session.id}")
    console.print(f"⏱️  Duration: {minutes} minutes")
    console.print(f"🔥 Nice work! Take a break!")


@main.command()
@click.option("--type", "break_type", default="short",
              type=click.Choice(["short", "long"]),
              help="Break type (short=5min, long=15min)")
@click.pass_context
def break_cmd(ctx, break_type):
    """Take a break."""
    tracker = ctx.obj["tracker"]

    duration = 5 if break_type == "short" else 15

    console.print(Panel.fit(
        f"[bold blue]{break_type.title()} Break[/bold blue]\n\nDuration: {duration} minutes\n\n"
        "Relax and recharge!",
        border_style="blue"
    ))

    total_seconds = duration * 60

    with Progress(
        "[progress.description]{task.description}",
        BarColumn(),
        "[progress.percentage]{task.percentage:>3.0f}%",
        TimeRemainingColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("On break...", total=total_seconds)

        for i in range(total_seconds, 0, -1):
            progress.update(task, completed=total_seconds - i)
            time.sleep(1)

    tracker.start_break(break_type=break_type, duration_minutes=duration)

    console.print(f"\n✅ Break over! Ready to focus again?")


@main.command()
@click.option("--days", "-d", default=7, help="Number of days to show stats for")
@click.pass_context
def stats(ctx, days):
    """Show productivity statistics."""
    tracker = ctx.obj["tracker"]
    stats = tracker.get_stats(days=days)
    streak = tracker.get_current_streak()

    console.print(Panel.fit(
        f"[bold cyan]Pomodoro Statistics[/bold cyan]\n\n"
        f"Period: Last {days} days\n\n"
        f"Total Focus Sessions: {stats['total_focus_sessions']}\n"
        f"Total Focus Time: {stats['total_focus_minutes']} minutes\n"
        f"Average per Day: {stats['average_per_day']} sessions\n"
        f"🔥 Current Streak: {streak} days",
        border_style="cyan"
    ))

    if stats["daily"]:
        console.print("\n📅 Daily Breakdown:")
        table = Table(show_header=True)
        table.add_column("Date", style="cyan")
        table.add_column("Sessions", style="green")
        table.add_column("Minutes", style="yellow")

        for date, data in sorted(stats["daily"].items())[-7:]:
            table.add_row(date, str(data["count"]), str(data["minutes"]))

        console.print(table)


if __name__ == "__main__":
    import time
    main()
