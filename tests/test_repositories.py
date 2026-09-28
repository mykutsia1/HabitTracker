"""Unit and integration tests for database connection and repositories."""

import unittest
from datetime import date, timedelta

from habit_tracker.core.exceptions import HabitNotFoundError
from habit_tracker.core.models import FrequencyType, Habit
from habit_tracker.database.connection import DatabaseManager
from habit_tracker.repositories.entry_repository import EntryRepository
from habit_tracker.repositories.habit_repository import HabitRepository


class TestRepositories(unittest.TestCase):
    """Test suite for Habit and Entry repositories with in-memory SQLite."""

    def setUp(self) -> None:
        self.db = DatabaseManager(":memory:")
        self.habit_repo = HabitRepository(self.db)
        self.entry_repo = EntryRepository(self.db)

    def test_habit_crud_and_archive(self) -> None:
        # 1. Create
        habit = Habit(
            name="Morning Meditation",
            description="10 mins mindfulness",
            category="Mindfulness",
            color="#10B981",
            frequency_type=FrequencyType.DAILY,
        )
        created = self.habit_repo.create(habit)
        self.assertIsNotNone(created.id)
        self.assertEqual(created.name, "Morning Meditation")

        # 2. Read by ID
        fetched = self.habit_repo.get_by_id(created.id)
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched.name, "Morning Meditation")
        self.assertEqual(fetched.category, "Mindfulness")

        # 3. List active
        active_list = self.habit_repo.list_active()
        self.assertEqual(len(active_list), 1)

        # 4. Update
        created.name = "Evening Meditation"
        created.category = "Health"
        updated = self.habit_repo.update(created)
        self.assertEqual(updated.name, "Evening Meditation")
        self.assertEqual(updated.category, "Health")

        # 5. Archive
        self.habit_repo.set_archived(created.id, archived=True)
        self.assertEqual(len(self.habit_repo.list_active()), 0)
        archived_list = self.habit_repo.list_archived()
        self.assertEqual(len(archived_list), 1)
        self.assertEqual(archived_list[0].id, created.id)

        # 6. Restore
        self.habit_repo.set_archived(created.id, archived=False)
        self.assertEqual(len(self.habit_repo.list_active()), 1)

        # 7. Delete
        self.habit_repo.delete(created.id)
        self.assertIsNone(self.habit_repo.get_by_id(created.id))
        self.assertEqual(len(self.habit_repo.list_active()), 0)

    def test_entry_toggle_and_range_queries(self) -> None:
        habit = self.habit_repo.create(Habit(name="Drink Water", frequency_type=FrequencyType.DAILY))
        today = date.today()
        yesterday = today - timedelta(days=1)

        # Initially empty
        entry_today = self.entry_repo.get_entry(habit.id, today)
        self.assertIsNone(entry_today)

        # Toggle to true
        updated = self.entry_repo.toggle_completion(habit.id, today)
        self.assertTrue(updated.completed)

        # Check completed dates
        completed_dates = self.entry_repo.get_completed_dates_for_habit(habit.id)
        self.assertIn(today, completed_dates)

        # Toggle to false
        updated_false = self.entry_repo.toggle_completion(habit.id, today)
        self.assertFalse(updated_false.completed)
        self.assertNotIn(today, self.entry_repo.get_completed_dates_for_habit(habit.id))

        # Set yesterday to completed
        self.entry_repo.set_completion(habit.id, yesterday, completed=True)
        completed_dates_after = self.entry_repo.get_completed_dates_for_habit(habit.id)
        self.assertIn(yesterday, completed_dates_after)

    def test_cascade_deletion(self) -> None:
        habit = self.habit_repo.create(Habit(name="Temporary Habit"))
        today = date.today()
        self.entry_repo.set_completion(habit.id, today, completed=True)

        self.assertEqual(len(self.entry_repo.get_completed_dates_for_habit(habit.id)), 1)
        self.habit_repo.delete(habit.id)

        # Entries should have been deleted via ON DELETE CASCADE
        self.assertEqual(len(self.entry_repo.get_completed_dates_for_habit(habit.id)), 0)


if __name__ == "__main__":
    unittest.main()
