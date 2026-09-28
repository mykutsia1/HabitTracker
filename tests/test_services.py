"""Unit tests for HabitService, StreakService, and AnalyticsService."""

import unittest
from datetime import date, timedelta

from habit_tracker.core.exceptions import ValidationError
from habit_tracker.core.models import FrequencyType, Habit
from habit_tracker.database.connection import DatabaseManager
from habit_tracker.repositories.entry_repository import EntryRepository
from habit_tracker.repositories.habit_repository import HabitRepository
from habit_tracker.services.analytics_service import AnalyticsService
from habit_tracker.services.habit_service import HabitService
from habit_tracker.services.streak_service import StreakService


class TestServices(unittest.TestCase):
    """Test suite for business logic and calculation algorithms."""

    def setUp(self) -> None:
        self.db = DatabaseManager(":memory:")
        self.habit_repo = HabitRepository(self.db)
        self.entry_repo = EntryRepository(self.db)
        self.streak_service = StreakService(self.entry_repo)
        self.habit_service = HabitService(self.habit_repo, self.entry_repo, self.streak_service)
        self.analytics_service = AnalyticsService(self.habit_repo, self.entry_repo, self.streak_service)

    def test_habit_service_validation(self) -> None:
        # Blank name
        with self.assertRaises(ValidationError):
            self.habit_service.create_habit(name="   ")

        # Invalid color
        with self.assertRaises(ValidationError):
            self.habit_service.create_habit(name="Valid Name", color="not-a-color")

        # Custom frequency without target days
        with self.assertRaises(ValidationError):
            self.habit_service.create_habit(
                name="Workout",
                frequency_type=FrequencyType.CUSTOM,
                target_days=[],
            )

        # Successful creation
        habit = self.habit_service.create_habit(name="Read Book", category="Learning")
        self.assertIsNotNone(habit.id)
        self.assertEqual(habit.name, "Read Book")

    def test_daily_streak_calculation(self) -> None:
        habit = self.habit_service.create_habit(
            name="Daily Pushups", frequency_type=FrequencyType.DAILY
        )
        today = date.today()
        d_minus_1 = today - timedelta(days=1)
        d_minus_2 = today - timedelta(days=2)
        d_minus_3 = today - timedelta(days=3)

        # 0 entries -> streak 0
        info = self.streak_service.calculate_streak(habit, reference_date=today)
        self.assertEqual(info.current_streak, 0)
        self.assertEqual(info.best_streak, 0)

        # Complete yesterday only: today is not yet completed, but grace applies!
        self.entry_repo.set_completion(habit.id, d_minus_1, completed=True)
        info = self.streak_service.calculate_streak(habit, reference_date=today)
        self.assertEqual(info.current_streak, 1)

        # Complete today as well: streak is now 2
        self.entry_repo.set_completion(habit.id, today, completed=True)
        info = self.streak_service.calculate_streak(habit, reference_date=today)
        self.assertEqual(info.current_streak, 2)
        self.assertEqual(info.best_streak, 2)

        # Complete 2 days ago as well: streak is 3
        self.entry_repo.set_completion(habit.id, d_minus_2, completed=True)
        info = self.streak_service.calculate_streak(habit, reference_date=today)
        self.assertEqual(info.current_streak, 3)
        self.assertEqual(info.best_streak, 3)

    def test_streak_reset_and_historical_best(self) -> None:
        habit = self.habit_service.create_habit(
            name="Floss Teeth", frequency_type=FrequencyType.DAILY
        )
        today = date.today()

        # Build a past 4-day streak: days -10, -9, -8, -7
        for d in range(7, 11):
            past_date = today - timedelta(days=d)
            self.entry_repo.set_completion(habit.id, past_date, completed=True)

        # Days -6, -5, -4, -3 were missed!
        # Now complete yesterday and today: 2-day current streak
        self.entry_repo.set_completion(habit.id, today - timedelta(days=1), completed=True)
        self.entry_repo.set_completion(habit.id, today, completed=True)

        info = self.streak_service.calculate_streak(habit, reference_date=today)
        self.assertEqual(info.current_streak, 2)
        self.assertEqual(info.best_streak, 4)

    def test_custom_frequency_streak(self) -> None:
        # Schedule on Mondays (0) and Wednesdays (2)
        habit = self.habit_service.create_habit(
            name="Bi-weekly Sprint",
            frequency_type=FrequencyType.CUSTOM,
            target_days=[0, 2],
        )

        # Let's find recent Monday and Wednesday
        today = date.today()
        # Anchor to a fixed Monday: 2026-09-14 (Mon), 2026-09-16 (Wed)
        mon = date(2026, 9, 14)
        tue = date(2026, 9, 15)
        wed = date(2026, 9, 16)

        # Mon completed, Wed completed, Tue was not scheduled
        self.entry_repo.set_completion(habit.id, mon, completed=True)
        self.entry_repo.set_completion(habit.id, wed, completed=True)

        info = self.streak_service.calculate_streak(habit, reference_date=wed)
        self.assertEqual(info.current_streak, 2)
        self.assertEqual(info.best_streak, 2)

    def test_analytics_service(self) -> None:
        habit1 = self.habit_service.create_habit(
            name="Meditate", frequency_type=FrequencyType.DAILY
        )
        habit2 = self.habit_service.create_habit(
            name="Run", frequency_type=FrequencyType.DAILY
        )
        today = date.today()

        # Habit 1 completed for last 7 days
        for i in range(7):
            self.entry_repo.set_completion(habit1.id, today - timedelta(days=i), completed=True)

        # Habit 2 completed only today
        self.entry_repo.set_completion(habit2.id, today, completed=True)

        # 7-day stats for habit1: 7 / 7 = 100%
        stats_h1 = self.analytics_service.get_completion_stats_for_window(habit1, 7, end_date=today)
        self.assertEqual(stats_h1.total_scheduled, 7)
        self.assertEqual(stats_h1.total_completed, 7)
        self.assertEqual(stats_h1.rate_percentage, 100.0)

        # 7-day stats aggregate (both habits):
        # Scheduled: 7 + 7 = 14. Completed: 7 + 1 = 8.
        # Rate: (8 / 14) * 100 = 57.1%
        stats_all = self.analytics_service.get_completion_stats_for_window(None, 7, end_date=today)
        self.assertEqual(stats_all.total_scheduled, 14)
        self.assertEqual(stats_all.total_completed, 8)
        self.assertEqual(stats_all.rate_percentage, 57.1)

        # Heatmap grid generation
        grid = self.analytics_service.get_heatmap_grid(weeks=12, end_date=today)
        self.assertEqual(len(grid), 7)  # 7 days of week
        self.assertEqual(len(grid[0]), 12)  # 12 weeks


if __name__ == "__main__":
    unittest.main()
