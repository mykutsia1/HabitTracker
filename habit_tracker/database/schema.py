"""Database DDL schemas and index definitions for Habit Tracker."""

CREATE_HABITS_TABLE = """
CREATE TABLE IF NOT EXISTS habits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    category TEXT NOT NULL DEFAULT 'General',
    color TEXT NOT NULL DEFAULT '#6366F1',
    frequency_type TEXT NOT NULL DEFAULT 'daily',
    target_days TEXT NOT NULL DEFAULT '[0, 1, 2, 3, 4, 5, 6]',
    archived INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
"""

CREATE_ENTRIES_TABLE = """
CREATE TABLE IF NOT EXISTS habit_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    habit_id INTEGER NOT NULL,
    entry_date TEXT NOT NULL,
    completed INTEGER NOT NULL DEFAULT 1,
    notes TEXT,
    logged_at TEXT NOT NULL,
    FOREIGN KEY (habit_id) REFERENCES habits (id) ON DELETE CASCADE,
    UNIQUE (habit_id, entry_date)
);
"""

CREATE_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_habits_archived ON habits (archived);",
    "CREATE INDEX IF NOT EXISTS idx_habits_category ON habits (category);",
    "CREATE INDEX IF NOT EXISTS idx_entries_habit_date ON habit_entries (habit_id, entry_date);",
    "CREATE INDEX IF NOT EXISTS idx_entries_date ON habit_entries (entry_date);",
    "CREATE INDEX IF NOT EXISTS idx_entries_completed ON habit_entries (completed);",
]
