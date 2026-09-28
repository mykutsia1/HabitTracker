"""Habit management view for listing, filtering, editing, archiving, and deleting habits."""

from typing import List, Optional

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from habit_tracker.core.models import Habit
from habit_tracker.services.habit_service import HabitService
from habit_tracker.services.streak_service import StreakService
from habit_tracker.ui.theme import (
    ACCENT_PRIMARY,
    BORDER_COLOR,
    DANGER_RED,
    TEXT_MUTED,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    WARNING_AMBER,
)


class HabitRowCard(QFrame):
    """Horizontal card representing a habit in management list."""

    edit_clicked = pyqtSignal(int)
    archive_clicked = pyqtSignal(int)
    delete_clicked = pyqtSignal(int)

    def __init__(self, habit: Habit, current_streak: int, best_streak: int, parent=None) -> None:
        super().__init__(parent)
        self.habit = habit
        self.habit_id = habit.id or 0
        self.setProperty("class", "Card")
        self.setFixedHeight(72)

        self.setStyleSheet(f"""
            HabitRowCard {{
                background-color: #151824;
                border: 1px solid {BORDER_COLOR};
                border-radius: 10px;
            }}
            HabitRowCard:hover {{
                border-color: #374151;
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 8, 16, 8)
        layout.setSpacing(16)

        # Color bar
        color_bar = QFrame()
        color_bar.setFixedSize(4, 36)
        color_bar.setStyleSheet(f"background-color: {habit.color}; border-radius: 2px;")
        layout.addWidget(color_bar)

        # Title & Category
        title_layout = QVBoxLayout()
        title_layout.setSpacing(2)
        title_layout.setContentsMargins(0, 4, 0, 4)

        name_lbl = QLabel(habit.name)
        name_lbl.setStyleSheet(f"font-size: 15px; font-weight: 600; color: {TEXT_PRIMARY};")
        title_layout.addWidget(name_lbl)

        sub_layout = QHBoxLayout()
        sub_layout.setSpacing(8)

        cat_lbl = QLabel(habit.category)
        cat_lbl.setStyleSheet(f"""
            font-size: 11px;
            font-weight: 600;
            color: {habit.color};
            background-color: rgba(99, 102, 241, 0.12);
            border-radius: 4px;
            padding: 2px 6px;
        """)
        sub_layout.addWidget(cat_lbl)

        freq_lbl = QLabel(f"•  {habit.target_days_display()}")
        freq_lbl.setStyleSheet(f"font-size: 11px; color: {TEXT_MUTED};")
        sub_layout.addWidget(freq_lbl)

        if habit.description:
            desc_lbl = QLabel(f"•  {habit.description}")
            desc_lbl.setStyleSheet(f"font-size: 11px; color: {TEXT_SECONDARY};")
            sub_layout.addWidget(desc_lbl)

        sub_layout.addStretch()
        title_layout.addLayout(sub_layout)
        layout.addLayout(title_layout, stretch=1)

        # Streaks Info
        streak_lbl = QLabel(f"🔥 {current_streak} d  (Best: {best_streak} d)")
        streak_lbl.setStyleSheet(f"""
            color: {WARNING_AMBER};
            font-size: 12px;
            font-weight: 600;
            padding: 4px 10px;
            background-color: rgba(245, 158, 11, 0.1);
            border-radius: 12px;
        """)
        layout.addWidget(streak_lbl)

        # Action Buttons
        edit_btn = QPushButton("Edit")
        edit_btn.setProperty("class", "SecondaryBtn")
        edit_btn.clicked.connect(lambda: self.edit_clicked.emit(self.habit_id))
        layout.addWidget(edit_btn)

        archive_text = "Restore" if habit.archived else "Archive"
        archive_btn = QPushButton(archive_text)
        archive_btn.setProperty("class", "SecondaryBtn")
        archive_btn.clicked.connect(lambda: self.archive_clicked.emit(self.habit_id))
        layout.addWidget(archive_btn)

        del_btn = QPushButton("Delete")
        del_btn.setProperty("class", "DangerBtn")
        del_btn.clicked.connect(lambda: self.delete_clicked.emit(self.habit_id))
        layout.addWidget(del_btn)


class HabitsManageView(QWidget):
    """Management view supporting CRUD actions, filtering, and tabbed active/archived lists."""

    new_habit_requested = pyqtSignal()
    edit_habit_requested = pyqtSignal(int)
    data_changed = pyqtSignal()

    def __init__(
        self,
        habit_service: HabitService,
        streak_service: StreakService,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.habit_service = habit_service
        self.streak_service = streak_service

        self._init_ui()
        self.refresh_data()

    def _init_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(28, 24, 28, 24)
        main_layout.setSpacing(16)

        # Header Title and New Habit Button
        header_row = QHBoxLayout()
        title_lbl = QLabel("Manage Habits")
        title_lbl.setStyleSheet(f"font-size: 22px; font-weight: 700; color: {TEXT_PRIMARY};")
        header_row.addWidget(title_lbl)
        header_row.addStretch()

        new_btn = QPushButton("+ New Habit")
        new_btn.setProperty("class", "PrimaryBtn")
        new_btn.clicked.connect(self.new_habit_requested.emit)
        header_row.addWidget(new_btn)
        main_layout.addLayout(header_row)

        # Filter & Search Toolbar
        filter_row = QHBoxLayout()
        filter_row.setSpacing(12)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search habits by name or description...")
        self.search_input.textChanged.connect(self._apply_filters)
        filter_row.addWidget(self.search_input, stretch=2)

        self.cat_filter = QComboBox()
        self.cat_filter.addItem("All Categories")
        self.cat_filter.currentTextChanged.connect(self._apply_filters)
        filter_row.addWidget(self.cat_filter, stretch=1)

        main_layout.addLayout(filter_row)

        # Tabs for Active and Archived Habits
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: none;
                background-color: transparent;
            }}
            QTabBar::tab {{
                background-color: #151824;
                color: {TEXT_SECONDARY};
                padding: 8px 18px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                font-weight: 600;
                margin-right: 4px;
            }}
            QTabBar::tab:selected {{
                background-color: {ACCENT_PRIMARY};
                color: #FFFFFF;
            }}
        """)

        # Active habits tab
        self.active_container = QWidget()
        self.active_layout = QVBoxLayout(self.active_container)
        self.active_layout.setContentsMargins(0, 12, 0, 0)
        self.active_layout.setSpacing(10)
        self.active_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        active_scroll = QScrollArea()
        active_scroll.setWidgetResizable(True)
        active_scroll.setFrameShape(QFrame.Shape.NoFrame)
        active_scroll.setWidget(self.active_container)
        self.tabs.addTab(active_scroll, "Active Habits")

        # Archived habits tab
        self.archived_container = QWidget()
        self.archived_layout = QVBoxLayout(self.archived_container)
        self.archived_layout.setContentsMargins(0, 12, 0, 0)
        self.archived_layout.setSpacing(10)
        self.archived_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        archived_scroll = QScrollArea()
        archived_scroll.setWidgetResizable(True)
        archived_scroll.setFrameShape(QFrame.Shape.NoFrame)
        archived_scroll.setWidget(self.archived_container)
        self.tabs.addTab(archived_scroll, "Archived Habits")

        main_layout.addWidget(self.tabs, stretch=1)

    def refresh_data(self) -> None:
        """Fetch categories and reload lists."""
        # Update categories combo
        current_cat = self.cat_filter.currentText()
        self.cat_filter.blockSignals(True)
        self.cat_filter.clear()
        self.cat_filter.addItem("All Categories")
        categories = self.habit_service.get_categories()
        for cat in categories:
            self.cat_filter.addItem(cat)

        idx = self.cat_filter.findText(current_cat)
        if idx >= 0:
            self.cat_filter.setCurrentIndex(idx)
        self.cat_filter.blockSignals(False)

        self._apply_filters()

    def _apply_filters(self) -> None:
        """Filter habits based on search text and category selection."""
        search_query = self.search_input.text().strip().lower()
        selected_cat = self.cat_filter.currentText()

        active_habits = self.habit_service.get_active_habits()
        archived_habits = self.habit_service.get_archived_habits()

        # Update tab titles with counts
        self.tabs.setTabText(0, f"Active Habits ({len(active_habits)})")
        self.tabs.setTabText(1, f"Archived ({len(archived_habits)})")

        self._render_list(self.active_layout, active_habits, search_query, selected_cat)
        self._render_list(self.archived_layout, archived_habits, search_query, selected_cat)

    def _render_list(
        self,
        layout: QVBoxLayout,
        habits: List[Habit],
        search_query: str,
        selected_cat: str,
    ) -> None:
        # Clear layout
        while layout.count() > 0:
            item = layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.setParent(None)

        filtered = []
        for h in habits:
            if selected_cat != "All Categories" and h.category != selected_cat:
                continue
            if search_query:
                match_name = search_query in h.name.lower()
                match_desc = search_query in h.description.lower()
                match_cat = search_query in h.category.lower()
                if not (match_name or match_desc or match_cat):
                    continue
            filtered.append(h)

        if not filtered:
            empty_lbl = QLabel("No habits matching current criteria.")
            empty_lbl.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 13px; padding: 24px;")
            empty_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(empty_lbl)
            return

        for habit in filtered:
            streak_info = self.streak_service.calculate_streak(habit)
            card = HabitRowCard(
                habit,
                streak_info.current_streak,
                streak_info.best_streak,
                self,
            )
            card.edit_clicked.connect(self.edit_habit_requested.emit)
            card.archive_clicked.connect(self._on_toggle_archive)
            card.delete_clicked.connect(self._on_delete_habit)
            layout.addWidget(card)

    def _on_toggle_archive(self, habit_id: int) -> None:
        habit = self.habit_service.get_habit(habit_id)
        if not habit:
            return
        if habit.archived:
            self.habit_service.restore_habit(habit_id)
        else:
            self.habit_service.archive_habit(habit_id)
        self.refresh_data()
        self.data_changed.emit()

    def _on_delete_habit(self, habit_id: int) -> None:
        habit = self.habit_service.get_habit(habit_id)
        if not habit:
            return

        reply = QMessageBox.question(
            self,
            "Confirm Deletion",
            f"Are you sure you want to permanently delete habit '{habit.name}'?\n"
            "This will delete all associated tracking history and cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.habit_service.delete_habit(habit_id)
            self.refresh_data()
            self.data_changed.emit()
