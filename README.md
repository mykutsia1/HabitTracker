# HabitPulse — Production-Ready Desktop Habit Tracker

A modern, offline-first desktop habit tracker built in Python 3.10+ using **PyQt6** and **SQLite**. Designed with a clean three-tier architecture, dynamic frequency-aware streak calculation, 7/30-day analytics, and a GitHub-style activity heat-grid.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)
![GUI](https://img.shields.io/badge/GUI-PyQt6-green.svg)
![Storage](https://img.shields.io/badge/Storage-SQLite-lightgrey.svg)
![Tests](https://img.shields.io/badge/Tests-14%20Passed-emerald.svg)

---

## Features

### 1. Habit Management (CRUD)
- **Flexible Scheduling**:
  - **Daily**: Track every day.
  - **Weekdays**: Mon – Fri (weekends automatically excluded).
  - **Custom Days**: Choose specific days (e.g. Mon, Wed, Fri for gym routines).
- **Organization**: Categories / tags (Health, Fitness, Learning, etc.) with custom color accents.
- **Full Lifecycle**: Add, edit, archive (soft-delete), and permanently delete habits with cascaded entry clean-up.

### 2. Daily Tracking Dashboard
- **Interactive Toggles**: Large interactive completion buttons with instant visual feedback (emerald fill, strikethrough, progress update).
- **Date Navigation**: Easily view and log completions for past days using `< Prev`, `Next >`, jump to `Today`, or the popup calendar picker.
- **Real-Time KPIs**:
  - Today's completion rate and visual progress bar.
  - Current top streak badge.
  - Rolling 7-day completion rate.

### 3. Analytics & Streaks
- **Dynamic Streak Engine**:
  - Accurately tracks **Current Streak** and **All-Time Best Streak**.
  - **Frequency-Aware**: Non-scheduled days (e.g. weekends for weekday-only habits) do not break streaks.
  - **Grace Period**: If today is scheduled but not yet logged, the streak remains intact based on the previous scheduled day.
- **Metrics**: Rolling 7-day and 30-day completion rates for both individual habits and overall aggregates.
- **GitHub-Style Activity Heat-Grid**:
  - Custom `QPainter`-based 18-week contribution grid with 5 visual intensity levels.
  - Interactive tooltips showing exact completion counts and percentages on hover.
  - Filterable across all habits or focused on a single habit.
- **Performance Leaderboard**: Ranks all active habits by current streak and monthly consistency.

### 4. Modern Dark Theme & Native Performance
- Sleek obsidian & indigo dark palette with smooth hover states, card layouts, and status notifications.
- High-DPI scaling support across Linux (Wayland / X11), macOS, and Windows.

---

## Architecture Overview

The application strictly decouples Database/Repository, Business Logic/Services, and UI Presentation layers:

```
HabitTracker/
├── habit_tracker/
│   ├── core/
│   │   ├── models.py           # Domain models: Habit, HabitEntry, FrequencyType, Stats
│   │   └── exceptions.py       # Custom domain exceptions (HabitNotFoundError, ValidationError)
│   ├── database/
│   │   ├── connection.py       # SQLite connection manager with WAL mode & PRAGMAs
│   │   └── schema.py           # DDL schemas and index creation
│   ├── repositories/
│   │   ├── habit_repository.py # Habit CRUD, category queries, and archiving
│   │   └── entry_repository.py # Daily completion logging, upserts, range queries
│   ├── services/
│   │   ├── habit_service.py    # Business rules, validation, daily item collation
│   │   ├── streak_service.py   # Frequency-aware current and all-time streak algorithms
│   │   └── analytics_service.py# Rolling 7/30-day rates, heat-grid matrix generation
│   └── ui/
│       ├── theme.py            # Dark theme QSS stylesheet & design tokens
│       ├── components/
│       │   ├── habit_card.py   # Interactive habit list item with toggle button
│       │   ├── date_nav.py     # Date navigation header with calendar popup
│       │   ├── stat_card.py    # KPI summary card with accent borders
│       │   └── heatmap.py      # Custom QPainter GitHub-style activity heat-grid
│       ├── dialogs/
│       │   └── habit_dialog.py # Create / Edit habit modal with validation
│       ├── views/
│       │   ├── dashboard_view.py    # Daily tracking & KPI summary view
│       │   ├── habits_manage_view.py# Full habit management, filters, and tabs
│       │   └── analytics_view.py    # Heatmap, trend stats, and streak leaderboard
│       └── main_window.py      # Main window with sidebar navigation & shortcuts
├── tests/
│   ├── test_models.py          # Domain model & frequency logic tests
│   ├── test_repositories.py    # Database & repository integration tests
│   ├── test_services.py        # Streak engine & analytics unit tests
│   └── test_ui.py              # Headless UI view wiring tests
├── main.py                     # CLI launcher & dependency injection bootstrap
├── requirements.txt            # Project dependencies (PyQt6)
└── README.md                   # Documentation
```

---

## Installation & Setup

### Prerequisites
- Python 3.10 or newer.

### 1. Clone the Repository
```bash
git clone https://github.com/mykutsia1/HabitTracker.git
cd HabitTracker
```

### 2. Create Virtual Environment and Install Dependencies

**Linux / macOS:**
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

**Windows (PowerShell):**
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

---

## Running the Application

### Launch Standard Application

**Linux / macOS:**
```bash
python3 main.py
# or: ./run.sh
```

**Windows:**
```powershell
python main.py
```
*(On first run, sample habits and realistic completion history are automatically seeded so you can immediately explore the dashboard, streaks, and heatmap!)*

### Command-Line Options
```bash
# Seed or reset with rich sample data
python main.py --seed-sample-data

# Use a custom SQLite database file
python main.py --db-path data/my_habits.db
```

---

## Keyboard Shortcuts

| Shortcut | Action |
| :--- | :--- |
| `Ctrl + N` | Open New Habit creation dialog |
| `Ctrl + 1` | Switch to **Daily Dashboard** view |
| `Ctrl + 2` | Switch to **Manage Habits** view |
| `Ctrl + 3` | Switch to **Analytics & Grid** view |

---

## Running the Test Suite

Run the full automated test suite (models, repositories, streak algorithms, analytics, and headless GUI tests):

```bash
python -m unittest discover -s tests -p "test_*.py" -v
```
