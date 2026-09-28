"""Unit tests for domain models and scheduling logic."""

import unittest
from datetime import date, datetime

from habit_tracker.core.models import (
    FrequencyType,
    Habit,
    HabitEntry,
    CompletionStats,
)


class TestHabitModels(unittest.TestCase):
    """Test suite for Habit entity behavior."""

    def test_frequency_daily(self) -> None:
        habit = Habit(name="Drink Water", frequency_type=FrequencyType.DAILY)
        # Check all days of a week
        # 2026-09-14 is Monday, 2026-09-20 is Sunday
        for d in range(14, 21):
            target = date(2026, 9, d)
            self.assertTrue(habit.is_scheduled_for_date(target))
        self.assertEqual(habit.target_days_display(), "Every day")

    def test_frequency_weekdays(self) -> None:
        habit = Habit(name="Read Code", frequency_type=FrequencyType.WEEKDAYS)
        # Monday to Friday should be scheduled
        for d in range(14, 19):  # Mon-Fri
            self.assertTrue(habit.is_scheduled_for_date(date(2026, 9, d)))
        # Saturday and Sunday should NOT be scheduled
        self.assertFalse(habit.is_scheduled_for_date(date(2026, 9, 19)))  # Sat
        self.assertFalse(habit.is_scheduled_for_date(date(2026, 9, 20)))  # Sun
        self.assertEqual(habit.target_days_display(), "Mon – Fri")

    def test_frequency_custom_days(self) -> None:
        # Mon (0), Wed (2), Fri (4)
        habit = Habit(
            name="Gym Workout",
            frequency_type=FrequencyType.CUSTOM,
            target_days=[0, 2, 4],
        )
        self.assertTrue(habit.is_scheduled_for_date(date(2026, 9, 14)))  # Mon
        self.assertFalse(habit.is_scheduled_for_date(date(2026, 9, 15)))  # Tue
        self.assertTrue(habit.is_scheduled_for_date(date(2026, 9, 16)))  # Wed
        self.assertFalse(habit.is_scheduled_for_date(date(2026, 9, 17)))  # Thu
        self.assertTrue(habit.is_scheduled_for_date(date(2026, 9, 18)))  # Fri
        self.assertFalse(habit.is_scheduled_for_date(date(2026, 9, 19)))  # Sat
        self.assertFalse(habit.is_scheduled_for_date(date(2026, 9, 20)))  # Sun
        self.assertEqual(habit.target_days_display(), "Mon, Wed, Fri")

    def test_completion_stats_percentage(self) -> None:
        stats_empty = CompletionStats(total_scheduled=0, total_completed=0)
        self.assertEqual(stats_empty.rate_percentage, 0.0)

        stats_half = CompletionStats(total_scheduled=10, total_completed=5)
        self.assertEqual(stats_half.rate_percentage, 50.0)

        stats_round = CompletionStats(total_scheduled=3, total_completed=1)
        self.assertEqual(stats_round.rate_percentage, 33.3)


if __name__ == "__main__":
    unittest.main()
