"""Analytics and metrics aggregation service."""

from datetime import date, timedelta
from typing import Any, Dict, List, Optional

from habit_tracker.core.models import CompletionStats, Habit, HeatmapCell
from habit_tracker.repositories.entry_repository import EntryRepository
from habit_tracker.repositories.habit_repository import HabitRepository
from habit_tracker.services.streak_service import StreakService


class AnalyticsService:
    """Calculates completion rates, streak metrics, and GitHub-style activity grid data."""

    def __init__(
        self,
        habit_repo: HabitRepository,
        entry_repo: EntryRepository,
        streak_service: StreakService,
    ) -> None:
        self.habit_repo = habit_repo
        self.entry_repo = entry_repo
        self.streak_service = streak_service

    def get_completion_stats_for_window(
        self, habit: Optional[Habit], days: int, end_date: Optional[date] = None
    ) -> CompletionStats:
        """Calculate aggregate scheduled vs completed counts over a rolling N-day window.

        Args:
            habit: Habit to evaluate, or None for aggregate across all active habits.
            days: Number of days in the lookback window (e.g. 7 or 30).
            end_date: Ending date of the window (inclusive, defaults to today).

        Returns:
            CompletionStats with total scheduled and completed instances.
        """
        ref_end = end_date or date.today()
        ref_start = ref_end - timedelta(days=days - 1)

        habits_to_check = [habit] if habit else self.habit_repo.list_active()
        if not habits_to_check:
            return CompletionStats(total_scheduled=0, total_completed=0)

        total_scheduled = 0
        total_completed = 0

        for h in habits_to_check:
            if h.id is None:
                continue
            completed_dates = self.entry_repo.get_completed_dates_for_habit(h.id)

            curr = ref_start
            while curr <= ref_end:
                if h.is_scheduled_for_date(curr):
                    total_scheduled += 1
                    if curr in completed_dates:
                        total_completed += 1
                curr += timedelta(days=1)

        return CompletionStats(total_scheduled=total_scheduled, total_completed=total_completed)

    def get_dashboard_summary(self, target_date: Optional[date] = None) -> Dict[str, Any]:
        """Aggregate high-level metrics for dashboard stat cards."""
        ref_date = target_date or date.today()
        active_habits = self.habit_repo.list_active()

        scheduled_today = [h for h in active_habits if h.is_scheduled_for_date(ref_date)]
        entries_today = self.entry_repo.get_entries_for_date(ref_date)

        completed_today_count = sum(
            1 for h in scheduled_today if h.id in entries_today and entries_today[h.id].completed
        )
        scheduled_today_count = len(scheduled_today)

        today_rate = (
            round((completed_today_count / scheduled_today_count) * 100.0, 1)
            if scheduled_today_count > 0
            else 0.0
        )

        stats_7d = self.get_completion_stats_for_window(None, 7, end_date=ref_date)
        stats_30d = self.get_completion_stats_for_window(None, 30, end_date=ref_date)

        best_active_streak = 0
        for h in active_habits:
            streak_info = self.streak_service.calculate_streak(h, reference_date=ref_date)
            if streak_info.current_streak > best_active_streak:
                best_active_streak = streak_info.current_streak

        return {
            "total_active_habits": len(active_habits),
            "scheduled_today_count": scheduled_today_count,
            "completed_today_count": completed_today_count,
            "today_rate": today_rate,
            "rate_7d": stats_7d.rate_percentage,
            "rate_30d": stats_30d.rate_percentage,
            "best_active_streak": best_active_streak,
        }

    def get_heatmap_grid(
        self, habit_id: Optional[int] = None, weeks: int = 16, end_date: Optional[date] = None
    ) -> List[List[HeatmapCell]]:
        """Generate a 7-row by N-column matrix of HeatmapCell objects.

        Row 0 is Monday, Row 6 is Sunday.
        Columns represent consecutive weeks leading up to end_date.

        Args:
            habit_id: Specific habit ID, or None for all active habits combined.
            weeks: Number of weeks to render.
            end_date: Ending date (defaults to today).

        Returns:
            List of 7 rows, where each row contains `weeks` HeatmapCell instances.
        """
        ref_end = end_date or date.today()

        # Align ref_end to the end of its week (Sunday) so grid columns align cleanly
        days_to_sunday = 6 - ref_end.weekday()
        grid_end = ref_end + timedelta(days=days_to_sunday)
        total_days = weeks * 7
        grid_start = grid_end - timedelta(days=total_days - 1)

        if habit_id is not None:
            target_habit = self.habit_repo.get_by_id(habit_id)
            habits = [target_habit] if target_habit else []
        else:
            habits = self.habit_repo.list_active()

        # Pre-fetch completed dates for all candidate habits
        habit_completions: Dict[int, set] = {}
        for h in habits:
            if h.id is not None:
                habit_completions[h.id] = self.entry_repo.get_completed_dates_for_habit(h.id)

        # Initialize 7 empty rows
        grid: List[List[HeatmapCell]] = [[] for _ in range(7)]

        curr = grid_start
        for _ in range(weeks):
            for day_idx in range(7):
                scheduled_count = 0
                completed_count = 0

                # Only evaluate if date does not exceed today / future
                if curr <= ref_end:
                    for h in habits:
                        if h.is_scheduled_for_date(curr):
                            scheduled_count += 1
                            if h.id is not None and curr in habit_completions.get(h.id, set()):
                                completed_count += 1

                # Calculate intensity level 0-4
                intensity = 0
                if scheduled_count > 0 and completed_count > 0:
                    pct = completed_count / scheduled_count
                    if pct < 0.33:
                        intensity = 1
                    elif pct < 0.67:
                        intensity = 2
                    elif pct < 1.0:
                        intensity = 3
                    else:
                        intensity = 4

                cell = HeatmapCell(
                    date=curr,
                    scheduled_count=scheduled_count,
                    completed_count=completed_count,
                    intensity=intensity,
                )
                grid[day_idx].append(cell)
                curr += timedelta(days=1)

        return grid

    def get_habit_leaderboard(self) -> List[Dict[str, Any]]:
        """Fetch active habits ranked by current streak descending."""
        habits = self.habit_repo.list_active()
        leaderboard = []

        for h in habits:
            streak_info = self.streak_service.calculate_streak(h)
            stats_30d = self.get_completion_stats_for_window(h, 30)
            leaderboard.append({
                "habit": h,
                "current_streak": streak_info.current_streak,
                "best_streak": streak_info.best_streak,
                "rate_30d": stats_30d.rate_percentage,
            })

        leaderboard.sort(key=lambda x: (x["current_streak"], x["best_streak"]), reverse=True)
        return leaderboard
