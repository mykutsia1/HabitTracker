"""Tests verifying UI initialization and view wiring in offscreen mode."""

import os
import unittest
from datetime import date

# Set offscreen platform to run headless in CI/test environments
os.environ["QT_QPA_PLATFORM"] = "offscreen"

from PyQt6.QtWidgets import QApplication

from habit_tracker.core.models import FrequencyType
from habit_tracker.database.connection import DatabaseManager
from habit_tracker.repositories.entry_repository import EntryRepository
from habit_tracker.repositories.habit_repository import HabitRepository
from habit_tracker.services.analytics_service import AnalyticsService
from habit_tracker.services.habit_service import HabitService
from habit_tracker.services.streak_service import StreakService
from habit_tracker.ui.main_window import MainWindow


class TestUIViews(unittest.TestCase):
    """Test suite ensuring UI views and components initialize and react without error."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self) -> None:
        self.db = DatabaseManager(":memory:")
        self.habit_repo = HabitRepository(self.db)
        self.entry_repo = EntryRepository(self.db)
        self.streak_service = StreakService(self.entry_repo)
        self.habit_service = HabitService(self.habit_repo, self.entry_repo, self.streak_service)
        self.analytics_service = AnalyticsService(self.habit_repo, self.entry_repo, self.streak_service)

    def test_main_window_lifecycle(self) -> None:
        # Create a habit first
        h = self.habit_service.create_habit(
            name="Morning Stretch",
            category="Health",
            frequency_type=FrequencyType.DAILY,
        )

        window = MainWindow(self.habit_service, self.streak_service, self.analytics_service)
        self.assertIsNotNone(window)

        # Verify initial view is dashboard
        self.assertEqual(window.stack.currentIndex(), 0)

        # Switch to Habits view
        window.switch_view(1)
        self.assertEqual(window.stack.currentIndex(), 1)

        # Switch to Analytics view
        window.switch_view(2)
        self.assertEqual(window.stack.currentIndex(), 2)

        # Switch back to Dashboard
        window.switch_view(0)
        self.assertEqual(window.stack.currentIndex(), 0)

        window.close()

    def test_dashboard_toggle_action(self) -> None:
        h = self.habit_service.create_habit(
            name="Drink Water",
            frequency_type=FrequencyType.DAILY,
        )
        today = date.today()

        window = MainWindow(self.habit_service, self.streak_service, self.analytics_service)
        dash = window.view_dashboard

        # Initially 0%
        self.assertEqual(dash.daily_progress.value(), 0)

        # Simulate toggle through view
        dash._on_habit_toggled(h.id)

        # Verify entry is completed in database
        entry = self.entry_repo.get_entry(h.id, today)
        self.assertIsNotNone(entry)
        self.assertTrue(entry.completed)

        # Verify progress bar updated to 100%
        self.assertEqual(dash.daily_progress.value(), 100)

        window.close()


if __name__ == "__main__":
    unittest.main()
