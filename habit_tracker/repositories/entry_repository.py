"""Repository handling database operations for daily habit completion entries."""

from datetime import date, datetime, timezone
from typing import Dict, List, Optional, Set

from habit_tracker.core.exceptions import DatabaseError
from habit_tracker.core.models import HabitEntry
from habit_tracker.database.connection import DatabaseManager


class EntryRepository:
    """Repository interface for persisting and querying daily HabitEntry logs."""

    def __init__(self, db_manager: DatabaseManager) -> None:
        self.db = db_manager

    def get_entry(self, habit_id: int, entry_date: date) -> Optional[HabitEntry]:
        """Fetch a specific habit completion entry for a date."""
        query = "SELECT * FROM habit_entries WHERE habit_id = ? AND entry_date = ?"
        try:
            with self.db.connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, (habit_id, entry_date.isoformat()))
                row = cursor.fetchone()
                if row:
                    return HabitEntry.from_row(row)
                return None
        except Exception as e:
            raise DatabaseError("Failed to fetch habit entry", str(e)) from e

    def set_completion(
        self,
        habit_id: int,
        entry_date: date,
        completed: bool,
        notes: Optional[str] = None,
    ) -> HabitEntry:
        """Upsert a completion status for a given habit and date."""
        now_str = datetime.now(timezone.utc).isoformat()
        date_str = entry_date.isoformat()
        query = """
        INSERT INTO habit_entries (habit_id, entry_date, completed, notes, logged_at)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(habit_id, entry_date) DO UPDATE SET
            completed = excluded.completed,
            notes = excluded.notes,
            logged_at = excluded.logged_at
        """
        params = (habit_id, date_str, 1 if completed else 0, notes, now_str)
        try:
            with self.db.connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                return HabitEntry(
                    id=cursor.lastrowid,
                    habit_id=habit_id,
                    entry_date=entry_date,
                    completed=completed,
                    notes=notes,
                    logged_at=datetime.fromisoformat(now_str),
                )
        except Exception as e:
            raise DatabaseError(f"Failed to record completion for habit {habit_id}", str(e)) from e

    def toggle_completion(
        self,
        habit_id: int,
        entry_date: date,
        notes: Optional[str] = None,
    ) -> HabitEntry:
        """Toggle the completion state for a given habit and date."""
        existing = self.get_entry(habit_id, entry_date)
        new_state = True if (existing is None or not existing.completed) else False
        return self.set_completion(habit_id, entry_date, new_state, notes or (existing.notes if existing else None))

    def get_entries_for_date(self, entry_date: date) -> Dict[int, HabitEntry]:
        """Fetch all entries for a specific date, mapped by habit_id."""
        query = "SELECT * FROM habit_entries WHERE entry_date = ?"
        try:
            with self.db.connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, (entry_date.isoformat(),))
                rows = cursor.fetchall()
                result: Dict[int, HabitEntry] = {}
                for row in rows:
                    entry = HabitEntry.from_row(row)
                    result[entry.habit_id] = entry
                return result
        except Exception as e:
            raise DatabaseError("Failed to fetch entries for date", str(e)) from e

    def get_completed_dates_for_habit(self, habit_id: int) -> Set[date]:
        """Return a set of all dates where this habit was completed."""
        query = "SELECT entry_date FROM habit_entries WHERE habit_id = ? AND completed = 1"
        try:
            with self.db.connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, (habit_id,))
                rows = cursor.fetchall()
                return {date.fromisoformat(row["entry_date"]) for row in rows}
        except Exception as e:
            raise DatabaseError(f"Failed to fetch completed dates for habit {habit_id}", str(e)) from e

    def get_entries_for_habit_in_range(
        self, habit_id: int, start_date: date, end_date: date
    ) -> List[HabitEntry]:
        """Fetch all entries for a habit within a closed date range [start_date, end_date]."""
        query = """
        SELECT * FROM habit_entries
        WHERE habit_id = ? AND entry_date >= ? AND entry_date <= ?
        ORDER BY entry_date ASC
        """
        try:
            with self.db.connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, (habit_id, start_date.isoformat(), end_date.isoformat()))
                return [HabitEntry.from_row(r) for r in cursor.fetchall()]
        except Exception as e:
            raise DatabaseError("Failed to fetch habit entries in range", str(e)) from e

    def get_all_completed_entries_in_range(
        self, start_date: date, end_date: date
    ) -> List[HabitEntry]:
        """Fetch all completed entries across all habits in a closed date range."""
        query = """
        SELECT * FROM habit_entries
        WHERE entry_date >= ? AND entry_date <= ? AND completed = 1
        ORDER BY entry_date ASC
        """
        try:
            with self.db.connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, (start_date.isoformat(), end_date.isoformat()))
                return [HabitEntry.from_row(r) for r in cursor.fetchall()]
        except Exception as e:
            raise DatabaseError("Failed to fetch entries in range", str(e)) from e

    def get_all_entries_for_habit(self, habit_id: int) -> List[HabitEntry]:
        """Fetch all entries for a habit ordered chronologically."""
        query = "SELECT * FROM habit_entries WHERE habit_id = ? ORDER BY entry_date ASC"
        try:
            with self.db.connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, (habit_id,))
                return [HabitEntry.from_row(r) for r in cursor.fetchall()]
        except Exception as e:
            raise DatabaseError("Failed to fetch all entries for habit", str(e)) from e
