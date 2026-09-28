"""Custom exceptions for the Habit Tracker application."""

from typing import Optional


class HabitTrackerError(Exception):
    """Base domain exception for Habit Tracker."""

    def __init__(self, message: str, details: Optional[str] = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details

    def __str__(self) -> str:
        if self.details:
            return f"{self.message}: {self.details}"
        return self.message


class HabitNotFoundError(HabitTrackerError):
    """Raised when a requested habit does not exist in the database."""

    def __init__(self, habit_id: int) -> None:
        super().__init__(f"Habit with ID {habit_id} not found.")
        self.habit_id = habit_id


class ValidationError(HabitTrackerError):
    """Raised when business input validation fails."""

    def __init__(self, field: str, message: str) -> None:
        super().__init__(f"Validation failed for '{field}': {message}")
        self.field = field


class DatabaseError(HabitTrackerError):
    """Raised when an unexpected database error occurs."""
    pass


class DuplicateEntryError(HabitTrackerError):
    """Raised when attempting to create a duplicate habit or log entry."""
    pass
