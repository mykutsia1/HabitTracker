"""Repository handling database CRUD operations for Habit entities."""

import json
from datetime import datetime, timezone
from typing import List, Optional

from habit_tracker.core.exceptions import DatabaseError, HabitNotFoundError
from habit_tracker.core.models import Habit
from habit_tracker.database.connection import DatabaseManager


class HabitRepository:
    """Repository interface for persisting and querying Habit entities."""

    def __init__(self, db_manager: DatabaseManager) -> None:
        self.db = db_manager

    def create(self, habit: Habit) -> Habit:
        """Insert a new habit record into the database.

        Args:
            habit: Habit entity to insert.

        Returns:
            The persisted Habit with its auto-generated ID.
        """
        now_str = datetime.now(timezone.utc).isoformat()
        query = """
        INSERT INTO habits (
            name, description, category, color, frequency_type, target_days,
            archived, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            habit.name.strip(),
            habit.description.strip(),
            habit.category.strip() or "General",
            habit.color,
            habit.frequency_type.value,
            json.dumps(habit.target_days),
            1 if habit.archived else 0,
            now_str,
            now_str,
        )
        try:
            with self.db.connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                habit.id = cursor.lastrowid
                habit.created_at = datetime.fromisoformat(now_str)
                habit.updated_at = datetime.fromisoformat(now_str)
                return habit
        except Exception as e:
            raise DatabaseError("Failed to create habit", str(e)) from e

    def get_by_id(self, habit_id: int) -> Optional[Habit]:
        """Fetch a habit by its primary key."""
        query = "SELECT * FROM habits WHERE id = ?"
        try:
            with self.db.connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, (habit_id,))
                row = cursor.fetchone()
                if row:
                    return Habit.from_row(row)
                return None
        except Exception as e:
            raise DatabaseError(f"Failed to fetch habit {habit_id}", str(e)) from e

    def list_active(self, category: Optional[str] = None) -> List[Habit]:
        """Fetch all active (non-archived) habits, ordered by category then name."""
        if category and category.lower() != "all":
            query = "SELECT * FROM habits WHERE archived = 0 AND category = ? ORDER BY category, name"
            params = (category,)
        else:
            query = "SELECT * FROM habits WHERE archived = 0 ORDER BY category, name"
            params = ()

        try:
            with self.db.connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                rows = cursor.fetchall()
                return [Habit.from_row(r) for r in rows]
        except Exception as e:
            raise DatabaseError("Failed to list active habits", str(e)) from e

    def list_archived(self) -> List[Habit]:
        """Fetch all archived habits."""
        query = "SELECT * FROM habits WHERE archived = 1 ORDER BY updated_at DESC"
        try:
            with self.db.connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query)
                rows = cursor.fetchall()
                return [Habit.from_row(r) for r in rows]
        except Exception as e:
            raise DatabaseError("Failed to list archived habits", str(e)) from e

    def list_all(self) -> List[Habit]:
        """Fetch all habits regardless of archive status."""
        query = "SELECT * FROM habits ORDER BY archived ASC, category, name"
        try:
            with self.db.connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query)
                rows = cursor.fetchall()
                return [Habit.from_row(r) for r in rows]
        except Exception as e:
            raise DatabaseError("Failed to list all habits", str(e)) from e

    def update(self, habit: Habit) -> Habit:
        """Update an existing habit record."""
        if habit.id is None:
            raise HabitNotFoundError(0)

        now_str = datetime.now(timezone.utc).isoformat()
        query = """
        UPDATE habits SET
            name = ?,
            description = ?,
            category = ?,
            color = ?,
            frequency_type = ?,
            target_days = ?,
            archived = ?,
            updated_at = ?
        WHERE id = ?
        """
        params = (
            habit.name.strip(),
            habit.description.strip(),
            habit.category.strip() or "General",
            habit.color,
            habit.frequency_type.value,
            json.dumps(habit.target_days),
            1 if habit.archived else 0,
            now_str,
            habit.id,
        )
        try:
            with self.db.connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                if cursor.rowcount == 0:
                    raise HabitNotFoundError(habit.id)
                habit.updated_at = datetime.fromisoformat(now_str)
                return habit
        except HabitNotFoundError:
            raise
        except Exception as e:
            raise DatabaseError(f"Failed to update habit {habit.id}", str(e)) from e

    def set_archived(self, habit_id: int, archived: bool) -> bool:
        """Archive or restore a habit."""
        now_str = datetime.now(timezone.utc).isoformat()
        query = "UPDATE habits SET archived = ?, updated_at = ? WHERE id = ?"
        try:
            with self.db.connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, (1 if archived else 0, now_str, habit_id))
                if cursor.rowcount == 0:
                    raise HabitNotFoundError(habit_id)
                return True
        except HabitNotFoundError:
            raise
        except Exception as e:
            raise DatabaseError(f"Failed to set archive status for habit {habit_id}", str(e)) from e

    def delete(self, habit_id: int) -> bool:
        """Hard-delete a habit and cascade-delete its completion entries."""
        query = "DELETE FROM habits WHERE id = ?"
        try:
            with self.db.connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, (habit_id,))
                if cursor.rowcount == 0:
                    raise HabitNotFoundError(habit_id)
                return True
        except HabitNotFoundError:
            raise
        except Exception as e:
            raise DatabaseError(f"Failed to delete habit {habit_id}", str(e)) from e

    def get_distinct_categories(self) -> List[str]:
        """Return list of distinct categories currently in use."""
        query = "SELECT DISTINCT category FROM habits WHERE archived = 0 ORDER BY category"
        try:
            with self.db.connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query)
                return [row["category"] for row in cursor.fetchall() if row["category"]]
        except Exception as e:
            raise DatabaseError("Failed to fetch distinct categories", str(e)) from e
