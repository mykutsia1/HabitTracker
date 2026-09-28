"""Business logic and validation service for habit management."""

import re
from datetime import date
from typing import List, Optional

from habit_tracker.core.exceptions import ValidationError
from habit_tracker.core.models import DailyHabitItem, FrequencyType, Habit
from habit_tracker.repositories.entry_repository import EntryRepository
from habit_tracker.repositories.habit_repository import HabitRepository
from habit_tracker.services.streak_service import StreakService

HEX_COLOR_REGEX = re.compile(r"^#(?:[0-9a-fA-F]{3}){1,2}$")


class HabitService:
    """Service encapsulating business rules, validations, and habit lifecycle workflows."""

    def __init__(
        self,
        habit_repo: HabitRepository,
        entry_repo: EntryRepository,
        streak_service: StreakService,
    ) -> None:
        self.habit_repo = habit_repo
        self.entry_repo = entry_repo
        self.streak_service = streak_service

    def validate_habit(self, habit: Habit) -> None:
        """Validate business invariants for a Habit.

        Raises:
            ValidationError: If any field fails domain rules.
        """
        name = habit.name.strip()
        if not name:
            raise ValidationError("name", "Habit name cannot be blank.")
        if len(name) > 100:
            raise ValidationError("name", "Habit name cannot exceed 100 characters.")

        if habit.category and len(habit.category.strip()) > 50:
            raise ValidationError("category", "Category cannot exceed 50 characters.")

        if habit.color and not HEX_COLOR_REGEX.match(habit.color):
            raise ValidationError("color", f"Invalid hex color format: '{habit.color}'.")

        if habit.frequency_type == FrequencyType.CUSTOM:
            if not habit.target_days:
                raise ValidationError("target_days", "At least one target day must be selected for custom frequency.")
            for day_idx in habit.target_days:
                if day_idx < 0 or day_idx > 6:
                    raise ValidationError("target_days", f"Invalid weekday index: {day_idx}. Must be between 0 (Mon) and 6 (Sun).")

    def create_habit(
        self,
        name: str,
        category: str = "General",
        description: str = "",
        color: str = "#6366F1",
        frequency_type: FrequencyType = FrequencyType.DAILY,
        target_days: Optional[List[int]] = None,
    ) -> Habit:
        """Validate and create a new habit."""
        if target_days is None:
            if frequency_type == FrequencyType.DAILY:
                target_days = [0, 1, 2, 3, 4, 5, 6]
            elif frequency_type == FrequencyType.WEEKDAYS:
                target_days = [0, 1, 2, 3, 4]
            else:
                target_days = [0, 1, 2, 3, 4, 5, 6]

        habit = Habit(
            name=name.strip(),
            category=category.strip() or "General",
            description=description.strip(),
            color=color or "#6366F1",
            frequency_type=frequency_type,
            target_days=sorted(list(set(target_days))),
            archived=False,
        )
        self.validate_habit(habit)
        return self.habit_repo.create(habit)

    def update_habit(
        self,
        habit_id: int,
        name: str,
        category: str = "General",
        description: str = "",
        color: str = "#6366F1",
        frequency_type: FrequencyType = FrequencyType.DAILY,
        target_days: Optional[List[int]] = None,
    ) -> Habit:
        """Validate and update an existing habit."""
        existing = self.habit_repo.get_by_id(habit_id)
        if not existing:
            raise ValidationError("id", f"Habit with ID {habit_id} does not exist.")

        if target_days is None:
            if frequency_type == FrequencyType.DAILY:
                target_days = [0, 1, 2, 3, 4, 5, 6]
            elif frequency_type == FrequencyType.WEEKDAYS:
                target_days = [0, 1, 2, 3, 4]
            else:
                target_days = existing.target_days

        existing.name = name.strip()
        existing.category = category.strip() or "General"
        existing.description = description.strip()
        existing.color = color or "#6366F1"
        existing.frequency_type = frequency_type
        existing.target_days = sorted(list(set(target_days)))

        self.validate_habit(existing)
        return self.habit_repo.update(existing)

    def archive_habit(self, habit_id: int) -> bool:
        """Archive a habit (soft-delete)."""
        return self.habit_repo.set_archived(habit_id, archived=True)

    def restore_habit(self, habit_id: int) -> bool:
        """Restore an archived habit."""
        return self.habit_repo.set_archived(habit_id, archived=False)

    def delete_habit(self, habit_id: int) -> bool:
        """Permanently delete a habit."""
        return self.habit_repo.delete(habit_id)

    def get_habit(self, habit_id: int) -> Optional[Habit]:
        """Fetch a habit by ID."""
        return self.habit_repo.get_by_id(habit_id)

    def get_active_habits(self, category: Optional[str] = None) -> List[Habit]:
        """Retrieve all active habits."""
        return self.habit_repo.list_active(category=category)

    def get_archived_habits(self) -> List[Habit]:
        """Retrieve all archived habits."""
        return self.habit_repo.list_archived()

    def get_categories(self) -> List[str]:
        """Fetch list of all unique categories in active habits."""
        return self.habit_repo.get_distinct_categories()

    def get_daily_items_for_date(self, target_date: date) -> List[DailyHabitItem]:
        """Retrieve all habits scheduled for a given date, with completion status and streaks."""
        habits = self.habit_repo.list_active()
        entries_by_id = self.entry_repo.get_entries_for_date(target_date)

        items: List[DailyHabitItem] = []
        for habit in habits:
            if not habit.is_scheduled_for_date(target_date):
                continue

            entry = entries_by_id.get(habit.id) if habit.id is not None else None
            is_completed = bool(entry.completed) if entry else False

            streak_info = self.streak_service.calculate_streak(habit, reference_date=target_date)

            items.append(
                DailyHabitItem(
                    habit=habit,
                    is_completed=is_completed,
                    entry=entry,
                    current_streak=streak_info.current_streak,
                    best_streak=streak_info.best_streak,
                )
            )

        # Sort: Incomplete habits first, then by category, then by name
        items.sort(key=lambda x: (x.is_completed, x.habit.category.lower(), x.habit.name.lower()))
        return items

    def toggle_habit_completion(self, habit_id: int, target_date: date) -> DailyHabitItem:
        """Toggle completion for a habit on target_date and return the updated DailyHabitItem."""
        habit = self.habit_repo.get_by_id(habit_id)
        if not habit:
            raise ValidationError("habit_id", f"Habit {habit_id} not found.")

        updated_entry = self.entry_repo.toggle_completion(habit_id, target_date)
        streak_info = self.streak_service.calculate_streak(habit, reference_date=target_date)

        return DailyHabitItem(
            habit=habit,
            is_completed=updated_entry.completed,
            entry=updated_entry,
            current_streak=streak_info.current_streak,
            best_streak=streak_info.best_streak,
        )
