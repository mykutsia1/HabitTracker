"""Interactive habit card item for daily dashboard and tracking views."""

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMenu,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from habit_tracker.core.models import DailyHabitItem
from habit_tracker.ui.theme import (
    BORDER_COLOR,
    SUCCESS_EMERALD,
    TEXT_MUTED,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    WARNING_AMBER,
)


class HabitCard(QFrame):
    """Interactive card widget representing a scheduled habit on the dashboard."""

    toggled = pyqtSignal(int)            # habit_id
    edit_requested = pyqtSignal(int)     # habit_id
    archive_requested = pyqtSignal(int)  # habit_id
    delete_requested = pyqtSignal(int)   # habit_id

    def __init__(self, item: DailyHabitItem, parent=None) -> None:
        super().__init__(parent)
        self.item = item
        self.habit_id = item.habit.id or 0
        self.is_completed = item.is_completed

        self.setProperty("class", "Card")
        self.setFixedHeight(76)

        self._init_ui()
        self._apply_state()

    def _init_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 10, 16, 10)
        layout.setSpacing(14)

        # 1. Big Interactive Toggle Checkbox Button
        self.check_btn = QPushButton()
        self.check_btn.setFixedSize(36, 36)
        self.check_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.check_btn.clicked.connect(self._on_check_clicked)
        layout.addWidget(self.check_btn)

        # 2. Left Accent Indicator Pill (Color of habit)
        self.color_bar = QFrame()
        self.color_bar.setFixedSize(4, 38)
        self.color_bar.setStyleSheet(f"""
            background-color: {self.item.habit.color};
            border-radius: 2px;
        """)
        layout.addWidget(self.color_bar)

        # 3. Main Details (Name, Description / Cue)
        details_layout = QVBoxLayout()
        details_layout.setContentsMargins(0, 2, 0, 2)
        details_layout.setSpacing(2)

        self.name_lbl = QLabel(self.item.habit.name)
        self.name_lbl.setStyleSheet(f"""
            font-size: 15px;
            font-weight: 600;
            color: {TEXT_PRIMARY};
        """)
        details_layout.addWidget(self.name_lbl)

        sub_info_layout = QHBoxLayout()
        sub_info_layout.setSpacing(8)

        # Category Badge
        cat_lbl = QLabel(self.item.habit.category)
        cat_lbl.setStyleSheet(f"""
            font-size: 11px;
            font-weight: 600;
            color: {self.item.habit.color};
            background-color: rgba(99, 102, 241, 0.12);
            border-radius: 4px;
            padding: 2px 6px;
        """)
        sub_info_layout.addWidget(cat_lbl)

        # Frequency Schedule Label
        freq_lbl = QLabel(f"•  {self.item.habit.target_days_display()}")
        freq_lbl.setStyleSheet(f"""
            font-size: 11px;
            color: {TEXT_MUTED};
        """)
        sub_info_layout.addWidget(freq_lbl)

        if self.item.habit.description:
            desc_lbl = QLabel(f"•  {self.item.habit.description}")
            desc_lbl.setStyleSheet(f"font-size: 11px; color: {TEXT_SECONDARY};")
            sub_info_layout.addWidget(desc_lbl)

        sub_info_layout.addStretch()
        details_layout.addLayout(sub_info_layout)
        layout.addLayout(details_layout, stretch=1)

        # 4. Streak Indicator Pill
        streak_count = self.item.current_streak
        best_count = self.item.best_streak
        self.streak_btn = QPushButton(f"🔥 {streak_count}")
        self.streak_btn.setToolTip(f"Current Streak: {streak_count} days\nAll-Time Best: {best_count} days")
        self.streak_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: rgba(245, 158, 11, 0.12);
                color: {WARNING_AMBER};
                font-size: 12px;
                font-weight: 700;
                border: 1px solid rgba(245, 158, 11, 0.25);
                border-radius: 14px;
                padding: 4px 10px;
            }}
        """)
        layout.addWidget(self.streak_btn)

        # 5. More Action Options Menu
        self.menu_btn = QPushButton("⋮")
        self.menu_btn.setFixedSize(32, 32)
        self.menu_btn.setProperty("class", "SecondaryBtn")
        self.menu_btn.setStyleSheet("font-size: 16px; font-weight: bold; border: none;")
        self.menu_btn.clicked.connect(self._show_context_menu)
        layout.addWidget(self.menu_btn)

    def _apply_state(self) -> None:
        """Apply visual changes based on completion status."""
        if self.is_completed:
            self.setStyleSheet(f"""
                HabitCard {{
                    background-color: rgba(16, 185, 129, 0.06);
                    border: 1px solid rgba(16, 185, 129, 0.25);
                    border-radius: 12px;
                }}
            """)
            self.check_btn.setText("✓")
            self.check_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {SUCCESS_EMERALD};
                    color: #FFFFFF;
                    font-size: 18px;
                    font-weight: bold;
                    border: none;
                    border-radius: 18px;
                }}
                QPushButton:hover {{
                    background-color: #059669;
                }}
            """)
            self.name_lbl.setStyleSheet(f"""
                font-size: 15px;
                font-weight: 600;
                color: {TEXT_MUTED};
                text-decoration: line-through;
            """)
        else:
            self.setStyleSheet(f"""
                HabitCard {{
                    background-color: #151824;
                    border: 1px solid {BORDER_COLOR};
                    border-radius: 12px;
                }}
                HabitCard:hover {{
                    border-color: #374151;
                    background-color: #1A1D2B;
                }}
            """)
            self.check_btn.setText("")
            self.check_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: #23283B;
                    border: 2px solid {BORDER_COLOR};
                    border-radius: 18px;
                }}
                QPushButton:hover {{
                    border-color: {SUCCESS_EMERALD};
                    background-color: rgba(16, 185, 129, 0.15);
                }}
            """)
            self.name_lbl.setStyleSheet(f"""
                font-size: 15px;
                font-weight: 600;
                color: {TEXT_PRIMARY};
            """)

    def _on_check_clicked(self) -> None:
        # Emit signal to update database and toggle UI immediately
        self.toggled.emit(self.habit_id)

    def update_item(self, item: DailyHabitItem) -> None:
        """Update item data and refresh rendering."""
        self.item = item
        self.is_completed = item.is_completed
        self.name_lbl.setText(item.habit.name)
        self.streak_btn.setText(f"🔥 {item.current_streak}")
        self.streak_btn.setToolTip(f"Current Streak: {item.current_streak} days\nAll-Time Best: {item.best_streak} days")
        self._apply_state()

    def _show_context_menu(self) -> None:
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #23283B;
                border: 1px solid #2A3047;
                border-radius: 8px;
                padding: 4px;
            }
            QMenu::item {
                padding: 6px 18px;
                border-radius: 4px;
                color: #F8FAFC;
            }
            QMenu::item:selected {
                background-color: #6366F1;
                color: #FFFFFF;
            }
        """)

        edit_act = menu.addAction("✏️ Edit Habit")
        archive_act = menu.addAction("📦 Archive Habit")
        menu.addSeparator()
        delete_act = menu.addAction("🗑️ Delete Habit")

        action = menu.exec(self.menu_btn.mapToGlobal(self.menu_btn.rect().bottomLeft()))
        if action == edit_act:
            self.edit_requested.emit(self.habit_id)
        elif action == archive_act:
            self.archive_requested.emit(self.habit_id)
        elif action == delete_act:
            self.delete_requested.emit(self.habit_id)
