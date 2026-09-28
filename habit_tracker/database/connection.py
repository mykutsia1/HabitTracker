"""SQLite database connection management and transaction lifecycle."""

import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Generator, Optional, Union

from habit_tracker.core.exceptions import DatabaseError
from habit_tracker.database.schema import CREATE_ENTRIES_TABLE, CREATE_HABITS_TABLE, CREATE_INDEXES


class DatabaseManager:
    """Manages SQLite connections, schema initialization, and transactional safety."""

    def __init__(self, db_path: Optional[Union[str, Path]] = None) -> None:
        """Initialize the database manager.

        Args:
            db_path: Path to the SQLite file. If None, defaults to `data/habits.db`
                     relative to the current working directory, or `:memory:` for testing.
        """
        if db_path is None:
            base_dir = Path(os.environ.get("HABIT_TRACKER_DATA_DIR", "data"))
            base_dir.mkdir(parents=True, exist_ok=True)
            self.db_path = str(base_dir / "habits.db")
        else:
            self.db_path = str(db_path)
            if self.db_path != ":memory:":
                Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._is_memory = (self.db_path == ":memory:")
        self._memory_conn: Optional[sqlite3.Connection] = None
        if self._is_memory:
            self._memory_conn = self._configure_connection(sqlite3.connect(":memory:", timeout=10.0))

        self.initialize_schema()

    def _configure_connection(self, conn: sqlite3.Connection) -> sqlite3.Connection:
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        if not self._is_memory:
            conn.execute("PRAGMA journal_mode = WAL;")
        conn.execute("PRAGMA busy_timeout = 5000;")
        return conn

    def create_connection(self) -> sqlite3.Connection:
        """Create a new configured SQLite connection with row factories and PRAGMAs."""
        if self._is_memory and self._memory_conn is not None:
            return self._memory_conn
        try:
            conn = sqlite3.connect(self.db_path, timeout=10.0)
            return self._configure_connection(conn)
        except sqlite3.Error as e:
            raise DatabaseError("Failed to establish SQLite connection", str(e)) from e

    @contextmanager
    def connection(self) -> Generator[sqlite3.Connection, None, None]:
        """Context manager yielding a transactional SQLite connection."""
        if self._is_memory and self._memory_conn is not None:
            conn = self._memory_conn
            try:
                yield conn
                conn.commit()
            except Exception as e:
                conn.rollback()
                if isinstance(e, DatabaseError):
                    raise
                raise DatabaseError("Database transaction failed", str(e)) from e
        else:
            conn = self.create_connection()
            try:
                yield conn
                conn.commit()
            except Exception as e:
                conn.rollback()
                if isinstance(e, DatabaseError):
                    raise
                raise DatabaseError("Database transaction failed", str(e)) from e
            finally:
                conn.close()

    def initialize_schema(self) -> None:
        """Execute table and index creation scripts idempotently."""
        try:
            with self.connection() as conn:
                cursor = conn.cursor()
                cursor.execute(CREATE_HABITS_TABLE)
                cursor.execute(CREATE_ENTRIES_TABLE)
                for index_sql in CREATE_INDEXES:
                    cursor.execute(index_sql)
        except sqlite3.Error as e:
            raise DatabaseError("Schema initialization failed", str(e)) from e
