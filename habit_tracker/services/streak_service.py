"""Streak calculation engine supporting daily, weekday, and custom schedules."""

from datetime import date, timedelta
from typing import Optional, Set

from habit_tracker.core.models import Habit, HabitStreakInfo
from habit_tracker.repositories.entry_repository import EntryRepository


class StreakService:
    """Service responsible for calculating current and all-time best streaks."""

    def __init__(self, entry_repo: EntryRepository) -> None:
        self.entry_repo = entry_repo

    def calculate_streak(
        self, habit: Habit, reference_date: Optional[date] = None
    ) -> HabitStreakInfo:
        """Calculate current and best streak for a habit relative to reference_date.

        Args:
            habit: Habit to evaluate.
            reference_date: Anchor date (defaults to today).

        Returns:
            HabitStreakInfo containing current streak, best streak, and last completion date.
        """
        if habit.id is None:
            return HabitStreakInfo(habit_id=0, current_streak=0, best_streak=0)

        ref_date = reference_date or date.today()
        completed_dates = self.entry_repo.get_completed_dates_for_habit(habit.id)

        last_completed: Optional[date] = None
        if completed_dates:
            past_or_today_completed = [d for d in completed_dates if d <= ref_date]
            if past_or_today_completed:
                last_completed = max(past_or_today_completed)

        current_streak = self._compute_current_streak(habit, completed_dates, ref_date)
        best_streak = self._compute_best_streak(habit, completed_dates, ref_date)

        # Invariant: best_streak is at least current_streak
        best_streak = max(best_streak, current_streak)

        return HabitStreakInfo(
            habit_id=habit.id,
            current_streak=current_streak,
            best_streak=best_streak,
            last_completed_date=last_completed,
        )

    def _compute_current_streak(
        self, habit: Habit, completed_dates: Set[date], ref_date: date
    ) -> int:
        """Calculate the active continuous streak counting backwards from ref_date."""
        if not completed_dates:
            return 0

        streak = 0
        curr_date = ref_date

        # Check if reference date itself is scheduled
        if habit.is_scheduled_for_date(curr_date):
            if curr_date in completed_dates:
                streak += 1
                curr_date -= timedelta(days=1)
            else:
                # If ref_date is today or future, the user still has time today to complete it.
                # Grace period: streak is not broken yet; count from the previous scheduled day.
                if curr_date >= date.today():
                    curr_date -= timedelta(days=1)
                else:
                    # Past scheduled day was not completed -> streak broken
                    return 0
        else:
            # ref_date wasn't scheduled (e.g. habit is weekdays only, ref_date is Saturday/Sunday)
            curr_date -= timedelta(days=1)

        # Walk backward day by day to count consecutive completed scheduled days
        # Safeguard: don't look back more than 5 years (1825 days)
        max_lookback = 1825
        days_checked = 0

        while days_checked < max_lookback:
            days_checked += 1
            if habit.is_scheduled_for_date(curr_date):
                if curr_date in completed_dates:
                    streak += 1
                    curr_date -= timedelta(days=1)
                else:
                    # Scheduled day missed: streak ends
                    break
            else:
                # Day wasn't scheduled: skip without breaking streak
                curr_date -= timedelta(days=1)

        return streak

    def _compute_best_streak(
        self, habit: Habit, completed_dates: Set[date], ref_date: date
    ) -> int:
        """Calculate the longest all-time consecutive scheduled completions up to ref_date."""
        if not completed_dates:
            return 0

        # Determine start date: earliest completed date or habit creation date
        earliest_completed = min(completed_dates)
        start_date = min(earliest_completed, habit.created_at.date())

        # If earliest completed is after ref_date (e.g., all entries in future), no streak
        if start_date > ref_date:
            return 0

        max_streak = 0
        running_streak = 0

        curr_date = start_date
        while curr_date <= ref_date:
            if habit.is_scheduled_for_date(curr_date):
                if curr_date in completed_dates:
                    running_streak += 1
                    if running_streak > max_streak:
                        max_streak = running_streak
                else:
                    # If this is today and incomplete, do not break streak yet
                    if curr_date >= date.today():
                        pass
                    else:
                        running_streak = 0
            curr_date += timedelta(days=1)

        return max_streak
