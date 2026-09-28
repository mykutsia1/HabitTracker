"""Dashboard view for daily habit tracking and logging."""

from datetime import date
from typing import Dict, List, Optional

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from habit_tracker.core.models import DailyHabitItem, Habit
from habit_tracker.services.analytics_service import AnalyticsService
from habit_tracker.services.habit_service import HabitService
from habit_tracker.ui.components.date_nav import DateNavigator
from habit_tracker.ui.components.habit_card import HabitCard
from habit_tracker.ui.components.stat_card import StatCard
from habit_tracker.ui.theme import (
    ACCENT_PRIMARY,
    BORDER_COLOR,
    SUCCESS_EMERALD,
    TEXT_MUTED,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    WARNING_AMBER,
)


class DashboardView(QWidget):
    """Daily tracking view displaying scheduled habits for selected date."""

    new_habit_requested = pyqtSignal()
    edit_habit_requested = pyqtSignal(int)
    archive_habit_requested = pyqtSignal(int)
    delete_habit_requested = pyqtSignal(int)
    habit_status_changed = pyqtSignal()

    def __init__(
        self,
        habit_service: HabitService,
        analytics_service: AnalyticsService,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.habit_service = habit_service
        self.analytics_service = analytics_service
        self.current_date = date.today()
        self.selected_category: Optional[str] = None
        self.habit_cards: Dict[int, HabitCard] = {}

        self._init_ui()
        self.refresh_data()

    def _init_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(28, 24, 28, 24)
        main_layout.setSpacing(20)

        # 1. Top Header (Title, Date Navigator & Quick New Habit)
        header_layout = QHBoxLayout()
        header_layout.setSpacing(16)

        self.date_nav = DateNavigator(self.current_date, self)
        self.date_nav.date_changed.connect(self._on_date_changed)
        header_layout.addWidget(self.date_nav)

        new_btn = QPushButton("+ New Habit")
        new_btn.setProperty("class", "PrimaryBtn")
        new_btn.clicked.connect(self.new_habit_requested.emit)
        header_layout.addWidget(new_btn)

        main_layout.addLayout(header_layout)

        # 2. KPI Summary Cards Row
        stats_row = QHBoxLayout()
        stats_row.setSpacing(14)

        self.stat_today_rate = StatCard("Today's Progress", "0%", "0 of 0 done", SUCCESS_EMERALD)
        self.stat_best_streak = StatCard("Best Active Streak", "0 Days", "Current top streak", WARNING_AMBER)
        self.stat_7d_rate = StatCard("7-Day Rate", "0%", "Rolling weekly average", ACCENT_PRIMARY)

        stats_row.addWidget(self.stat_today_rate)
        stats_row.addWidget(self.stat_best_streak)
        stats_row.addWidget(self.stat_7d_rate)
        main_layout.addLayout(stats_row)

        # 3. Overall Daily Progress Bar
        self.progress_container = QFrame()
        prog_layout = QVBoxLayout(self.progress_container)
        prog_layout.setContentsMargins(0, 0, 0, 0)
        prog_layout.setSpacing(6)

        prog_header = QHBoxLayout()
        self.prog_lbl = QLabel("Day Completion Rate")
        self.prog_lbl.setStyleSheet(f"font-size: 12px; font-weight: 600; color: {TEXT_SECONDARY};")
        self.prog_pct_lbl = QLabel("0%")
        self.prog_pct_lbl.setStyleSheet(f"font-size: 12px; font-weight: 700; color: {SUCCESS_EMERALD};")
        prog_header.addWidget(self.prog_lbl)
        prog_header.addStretch()
        prog_header.addWidget(self.prog_pct_lbl)
        prog_layout.addLayout(prog_header)

        self.daily_progress = QProgressBar()
        self.daily_progress.setRange(0, 100)
        self.daily_progress.setValue(0)
        prog_layout.addWidget(self.daily_progress)
        main_layout.addWidget(self.progress_container)

        # 4. Habits List Scroll Area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_area.setStyleSheet("background-color: transparent;")

        self.cards_container = QWidget()
        self.cards_layout = QVBoxLayout(self.cards_container)
        self.cards_layout.setContentsMargins(0, 0, 0, 0)
        self.cards_layout.setSpacing(10)
        self.cards_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.scroll_area.setWidget(self.cards_container)
        main_layout.addWidget(self.scroll_area, stretch=1)

        # 5. Empty State Container
        self.empty_state = QFrame()
        self.empty_state.setStyleSheet(f"""
            QFrame {{
                background-color: #151824;
                border: 1px dashed {BORDER_COLOR};
                border-radius: 12px;
                padding: 40px;
            }}
        """)
        empty_layout = QVBoxLayout(self.empty_state)
        empty_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_layout.setSpacing(12)

        empty_icon = QLabel("🌱")
        empty_icon.setStyleSheet("font-size: 42px;")
        empty_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_layout.addWidget(empty_icon)

        empty_title = QLabel("No Habits Scheduled For This Day")
        empty_title.setStyleSheet(f"font-size: 16px; font-weight: 700; color: {TEXT_PRIMARY};")
        empty_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_layout.addWidget(empty_title)

        empty_sub = QLabel("Add a habit or change schedule to start tracking your daily progress.")
        empty_sub.setStyleSheet(f"font-size: 13px; color: {TEXT_MUTED};")
        empty_sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_layout.addWidget(empty_sub)

        empty_btn = QPushButton("+ Create New Habit")
        empty_btn.setProperty("class", "PrimaryBtn")
        empty_btn.clicked.connect(self.new_habit_requested.emit)
        empty_layout.addWidget(empty_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        self.cards_layout.addWidget(self.empty_state)

    def _on_date_changed(self, new_date: date) -> None:
        self.current_date = new_date
        self.refresh_data()

    def refresh_data(self) -> None:
        """Fetch updated items from service and rebuild card list."""
        items = self.habit_service.get_daily_items_for_date(self.current_date)
        summary = self.analytics_service.get_dashboard_summary(self.current_date)

        # Update KPI cards
        sched_count = summary["scheduled_today_count"]
        comp_count = summary["completed_today_count"]
        rate = summary["today_rate"]

        self.stat_today_rate.set_value(f"{rate}%", f"{comp_count} of {sched_count} completed")
        self.stat_best_streak.set_value(f"{summary['best_active_streak']} Days", "Current top streak")
        self.stat_7d_rate.set_value(f"{summary['rate_7d']}%", "Rolling weekly average")

        self.daily_progress.setValue(int(rate))
        self.prog_pct_lbl.setText(f"{rate}%")

        # Clear existing cards
        self.habit_cards.clear()
        while self.cards_layout.count() > 0:
            item = self.cards_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.setParent(None)

        if not items:
            self.cards_layout.addWidget(self.empty_state)
            self.empty_state.show()
            self.progress_container.hide()
        else:
            self.empty_state.hide()
            self.progress_container.show()

            for item in items:
                card = HabitCard(item, self.cards_container)
                card.toggled.connect(self._on_habit_toggled)
                card.edit_requested.connect(self.edit_habit_requested.emit)
                card.archive_requested.connect(self.archive_habit_requested.emit)
                card.delete_requested.connect(self.delete_habit_requested.emit)
                self.habit_cards[item.habit.id or 0] = card
                self.cards_layout.addWidget(card)

    def _on_habit_toggled(self, habit_id: int) -> None:
        """Toggle habit in service and update UI immediately."""
        updated_item = self.habit_service.toggle_habit_completion(habit_id, self.current_date)
        if habit_id in self.habit_cards:
            self.habit_cards[habit_id].update_item(updated_item)

        # Update summary KPIs
        summary = self.analytics_service.get_dashboard_summary(self.current_date)
        sched_count = summary["scheduled_today_count"]
        comp_count = summary["completed_today_count"]
        rate = summary["today_rate"]

        self.stat_today_rate.set_value(f"{rate}%", f"{comp_count} of {sched_count} completed")
        self.stat_best_streak.set_value(f"{summary['best_active_streak']} Days", "Current top streak")
        self.daily_progress.setValue(int(rate))
        self.prog_pct_lbl.setText(f"{rate}%")

        self.habit_status_changed.emit()
