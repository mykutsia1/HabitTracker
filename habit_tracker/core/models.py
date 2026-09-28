"""Domain models and value objects for the Habit Tracker application."""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Sequence


class FrequencyType(str, Enum):
    """Supported habit repetition frequencies."""
    DAILY = "daily"
    WEEKDAYS = "weekdays"
    CUSTOM = "custom"

    @classmethod
    def from_str(cls, value: str) -> FrequencyType:
        """Parse string to FrequencyType case-insensitively."""
        val = value.strip().lower()
        for member in cls:
            if member.value == val:
                return member
        raise ValueError(f"Unknown frequency type: '{value}'. Must be daily, weekdays, or custom.")


WEEKDAY_NAMES_SHORT = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
WEEKDAY_NAMES_FULL = [
    "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"
]


@dataclass
class Habit:
    """Represents a tracked habit entity."""
    id: Optional[int] = None
    name: str = ""
    description: str = ""
    category: str = "General"
    color: str = "#6366F1"  # Default Indigo accent
    frequency_type: FrequencyType = FrequencyType.DAILY
    target_days: List[int] = field(default_factory=lambda: [0, 1, 2, 3, 4, 5, 6])
    archived: bool = False
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def is_scheduled_for_date(self, target_date: date) -> bool:
        """Determine whether this habit is scheduled to be performed on a given date.
        
        Args:
            target_date: Calendar date to evaluate.

        Returns:
            True if the habit is scheduled for target_date, False otherwise.
        """
        weekday = target_date.weekday()  # 0=Monday, 6=Sunday
        if self.frequency_type == FrequencyType.DAILY:
            return True
        elif self.frequency_type == FrequencyType.WEEKDAYS:
            return weekday < 5  # Mon-Fri
        elif self.frequency_type == FrequencyType.CUSTOM:
            return weekday in self.target_days
        return False

    def target_days_display(self) -> str:
        """Return a human-readable representation of the repetition schedule."""
        if self.frequency_type == FrequencyType.DAILY:
            return "Every day"
        if self.frequency_type == FrequencyType.WEEKDAYS:
            return "Mon – Fri"
        if not self.target_days:
            return "No days scheduled"
        if len(self.target_days) == 7:
            return "Every day"
        if sorted(self.target_days) == [0, 1, 2, 3, 4]:
            return "Mon – Fri"
        if sorted(self.target_days) == [5, 6]:
            return "Weekends (Sat, Sun)"

        sorted_days = sorted(self.target_days)
        return ", ".join(WEEKDAY_NAMES_SHORT[d] for d in sorted_days)

    def to_dict(self) -> Dict[str, Any]:
        """Convert habit to dictionary representation."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "color": self.color,
            "frequency_type": self.frequency_type.value,
            "target_days": json.dumps(self.target_days),
            "archived": 1 if self.archived else 0,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> Habit:
        """Construct a Habit entity from an SQLite Row."""
        target_days_raw = row["target_days"]
        if isinstance(target_days_raw, str):
            try:
                target_days = json.loads(target_days_raw)
            except (json.JSONDecodeError, TypeError):
                target_days = [0, 1, 2, 3, 4, 5, 6]
        elif isinstance(target_days_raw, Sequence):
            target_days = list(target_days_raw)
        else:
            target_days = [0, 1, 2, 3, 4, 5, 6]

        created_at_val = row["created_at"]
        if isinstance(created_at_val, str):
            try:
                created_at = datetime.fromisoformat(created_at_val)
            except ValueError:
                created_at = datetime.now(timezone.utc)
        else:
            created_at = datetime.now(timezone.utc)

        updated_at_val = row["updated_at"]
        if isinstance(updated_at_val, str):
            try:
                updated_at = datetime.fromisoformat(updated_at_val)
            except ValueError:
                updated_at = datetime.now(timezone.utc)
        else:
            updated_at = datetime.now(timezone.utc)

        return cls(
            id=row["id"],
            name=row["name"],
            description=row["description"] or "",
            category=row["category"] or "General",
            color=row["color"] or "#6366F1",
            frequency_type=FrequencyType.from_str(row["frequency_type"]),
            target_days=target_days,
            archived=bool(row["archived"]),
            created_at=created_at,
            updated_at=updated_at,
        )


@dataclass
class HabitEntry:
    """Represents a daily completion log for a specific habit."""
    id: Optional[int] = None
    habit_id: int = 0
    entry_date: date = field(default_factory=date.today)
    completed: bool = True
    notes: Optional[str] = None
    logged_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        """Convert entry to dictionary representation."""
        return {
            "id": self.id,
            "habit_id": self.habit_id,
            "entry_date": self.entry_date.isoformat(),
            "completed": 1 if self.completed else 0,
            "notes": self.notes,
            "logged_at": self.logged_at.isoformat(),
        }

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> HabitEntry:
        """Construct a HabitEntry from an SQLite Row."""
        entry_date_val = row["entry_date"]
        if isinstance(entry_date_val, str):
            parsed_date = date.fromisoformat(entry_date_val)
        elif isinstance(entry_date_val, date):
            parsed_date = entry_date_val
        else:
            parsed_date = date.today()

        logged_at_val = row["logged_at"]
        if isinstance(logged_at_val, str):
            try:
                logged_at = datetime.fromisoformat(logged_at_val)
            except ValueError:
                logged_at = datetime.now(timezone.utc)
        else:
            logged_at = datetime.now(timezone.utc)

        return cls(
            id=row["id"],
            habit_id=row["habit_id"],
            entry_date=parsed_date,
            completed=bool(row["completed"]),
            notes=row["notes"] if "notes" in row.keys() else None,
            logged_at=logged_at,
        )


@dataclass
class HabitStreakInfo:
    """Streak statistics calculated for a specific habit."""
    habit_id: int
    current_streak: int = 0
    best_streak: int = 0
    last_completed_date: Optional[date] = None


@dataclass
class CompletionStats:
    """Aggregate completion statistics over a time window."""
    total_scheduled: int = 0
    total_completed: int = 0

    @property
    def rate_percentage(self) -> float:
        """Completion percentage (0.0 to 100.0)."""
        if self.total_scheduled == 0:
            return 0.0
        return round((self.total_completed / self.total_scheduled) * 100.0, 1)


@dataclass
class HeatmapCell:
    """Data item for rendering one cell on the GitHub-style activity grid."""
    date: date
    scheduled_count: int
    completed_count: int
    intensity: int  # 0 to 4 (0=none, 1=low, 2=medium, 3=high, 4=max)

    @property
    def rate_percentage(self) -> float:
        if self.scheduled_count == 0:
            return 0.0
        return round((self.completed_count / self.scheduled_count) * 100.0, 1)


@dataclass
class DailyHabitItem:
    """View model representing a habit scheduled for a specific date."""
    habit: Habit
    is_completed: bool = False
    entry: Optional[HabitEntry] = None
    current_streak: int = 0
    best_streak: int = 0
