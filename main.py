"""Application entry point and dependency injection bootstrap for HabitPulse."""

import argparse
import os
import sys
from datetime import date, timedelta
from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication

from habit_tracker.core.models import FrequencyType
from habit_tracker.database.connection import DatabaseManager
from habit_tracker.repositories.entry_repository import EntryRepository
from habit_tracker.repositories.habit_repository import HabitRepository
from habit_tracker.services.analytics_service import AnalyticsService
from habit_tracker.services.habit_service import HabitService
from habit_tracker.services.streak_service import StreakService
from habit_tracker.ui.main_window import MainWindow


def seed_sample_habits(habit_service: HabitService, entry_repo: EntryRepository) -> None:
    """Populate database with sample habits and realistic completion history."""
    today = date.today()

    # 1. Drink 2L Water (Daily, 14-day streak)
    h_water = habit_service.create_habit(
        name="Drink 2L Water",
        category="Health",
        description="Stay hydrated throughout the day",
        color="#0EA5E9",
        frequency_type=FrequencyType.DAILY,
    )
    for i in range(14):
        entry_repo.set_completion(h_water.id, today - timedelta(days=i), completed=True)

    # 2. Morning Meditation (Daily, 7-day streak)
    h_meditate = habit_service.create_habit(
        name="Morning Meditation",
        category="Mindfulness",
        description="10 minutes mindfulness practice",
        color="#8B5CF6",
        frequency_type=FrequencyType.DAILY,
    )
    for i in range(7):
        entry_repo.set_completion(h_meditate.id, today - timedelta(days=i), completed=True)

    # 3. Strength Training (Mon, Wed, Fri custom schedule)
    h_gym = habit_service.create_habit(
        name="Strength Workout",
        category="Fitness",
        description="45 minutes weightlifting session",
        color="#EF4444",
        frequency_type=FrequencyType.CUSTOM,
        target_days=[0, 2, 4],  # Mon, Wed, Fri
    )
    # Log past 30 days of workouts
    for d in range(30):
        past_d = today - timedelta(days=d)
        if h_gym.is_scheduled_for_date(past_d) and d % 3 != 0:
            entry_repo.set_completion(h_gym.id, past_d, completed=True)

    # 4. Read 20 Pages (Weekdays)
    h_read = habit_service.create_habit(
        name="Read 20 Pages",
        category="Learning",
        description="Non-fiction or technical book",
        color="#10B981",
        frequency_type=FrequencyType.WEEKDAYS,
    )
    for d in range(1, 10):
        past_d = today - timedelta(days=d)
        if h_read.is_scheduled_for_date(past_d):
            entry_repo.set_completion(h_read.id, past_d, completed=True)

    # 5. Nightly Journaling (Daily, new habit)
    habit_service.create_habit(
        name="Nightly Reflection",
        category="Mindfulness",
        description="3 things I'm grateful for today",
        color="#F59E0B",
        frequency_type=FrequencyType.DAILY,
    )


def main() -> None:
    """Main application launcher."""
    parser = argparse.ArgumentParser(description="HabitPulse - Production-Ready Desktop Habit Tracker")
    parser.add_argument(
        "--db-path",
        type=str,
        default=None,
        help="Custom path to SQLite database file (defaults to data/habits.db)",
    )
    parser.add_argument(
        "--seed-sample-data",
        action="store_true",
        help="Seed database with sample habits and tracking history",
    )
    args = parser.parse_args()

    # Enable High DPI scaling
    if hasattr(Qt.ApplicationAttribute, "AA_EnableHighDpiScaling"):
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)
    if hasattr(Qt.ApplicationAttribute, "AA_UseHighDpiPixmaps"):
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    app.setApplicationName("HabitPulse")
    app.setOrganizationName("Antigravity")

    # Dependency Injection Setup
    db_path = args.db_path or os.environ.get("HABIT_TRACKER_DB", "data/habits.db")
    db_manager = DatabaseManager(db_path)
    habit_repo = HabitRepository(db_manager)
    entry_repo = EntryRepository(db_manager)
    streak_service = StreakService(entry_repo)
    habit_service = HabitService(habit_repo, entry_repo, streak_service)
    analytics_service = AnalyticsService(habit_repo, entry_repo, streak_service)

    # Seed data if explicitly requested or if database is empty on first run
    existing_habits = habit_repo.list_all()
    if args.seed_sample_data or len(existing_habits) == 0:
        seed_sample_habits(habit_service, entry_repo)

    window = MainWindow(habit_service, streak_service, analytics_service)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
