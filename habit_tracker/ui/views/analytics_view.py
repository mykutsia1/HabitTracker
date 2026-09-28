"""Analytics view with GitHub-style activity grid, streak statistics, and completion metrics."""

from typing import Optional

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QScrollArea,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from habit_tracker.services.analytics_service import AnalyticsService
from habit_tracker.services.habit_service import HabitService
from habit_tracker.services.streak_service import StreakService
from habit_tracker.ui.components.heatmap import HeatmapWidget
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


class AnalyticsView(QWidget):
    """Analytics view featuring heatmaps, trend KPIs, and habit leaderboards."""

    def __init__(
        self,
        habit_service: HabitService,
        streak_service: StreakService,
        analytics_service: AnalyticsService,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.habit_service = habit_service
        self.streak_service = streak_service
        self.analytics_service = analytics_service

        self._init_ui()
        self.refresh_data()

    def _init_ui(self) -> None:
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("background-color: transparent;")

        container = QWidget()
        main_layout = QVBoxLayout(container)
        main_layout.setContentsMargins(28, 24, 28, 24)
        main_layout.setSpacing(24)

        # 1. Header & Habit Focus Filter
        header_row = QHBoxLayout()
        title_lbl = QLabel("Analytics & Insights")
        title_lbl.setStyleSheet(f"font-size: 22px; font-weight: 700; color: {TEXT_PRIMARY};")
        header_row.addWidget(title_lbl)
        header_row.addStretch()

        filter_label = QLabel("Focus Habit:")
        filter_label.setStyleSheet(f"color: {TEXT_SECONDARY}; font-weight: 600;")
        header_row.addWidget(filter_label)

        self.habit_selector = QComboBox()
        self.habit_selector.setMinimumWidth(220)
        self.habit_selector.addItem("All Habits (Overview)", userData=None)
        self.habit_selector.currentIndexChanged.connect(self._on_habit_selected)
        header_row.addWidget(self.habit_selector)

        main_layout.addLayout(header_row)

        # 2. KPI Metrics Cards
        kpi_row = QHBoxLayout()
        kpi_row.setSpacing(14)

        self.card_7d = StatCard("7-Day Rate", "0%", "Rolling weekly consistency", SUCCESS_EMERALD)
        self.card_30d = StatCard("30-Day Rate", "0%", "Monthly adherence", ACCENT_PRIMARY)
        self.card_curr_streak = StatCard("Current Streak", "0 Days", "Active consecutive completions", WARNING_AMBER)
        self.card_best_streak = StatCard("Best Streak", "0 Days", "All-time personal record", "#8B5CF6")

        kpi_row.addWidget(self.card_7d)
        kpi_row.addWidget(self.card_30d)
        kpi_row.addWidget(self.card_curr_streak)
        kpi_row.addWidget(self.card_best_streak)
        main_layout.addLayout(kpi_row)

        # 3. Heatmap Card Section
        heatmap_card = QFrame()
        heatmap_card.setProperty("class", "Card")
        heatmap_card.setStyleSheet(f"""
            QFrame {{
                background-color: #151824;
                border: 1px solid {BORDER_COLOR};
                border-radius: 12px;
                padding: 18px;
            }}
        """)
        heatmap_layout = QVBoxLayout(heatmap_card)
        heatmap_layout.setSpacing(12)

        heat_header = QLabel("Activity Heat-Grid (Past 18 Weeks)")
        heat_header.setStyleSheet(f"font-size: 15px; font-weight: 700; color: {TEXT_PRIMARY};")
        heatmap_layout.addWidget(heat_header)

        self.heatmap_widget = HeatmapWidget(cell_size=14, cell_spacing=4, parent=self)
        heatmap_layout.addWidget(self.heatmap_widget)
        main_layout.addWidget(heatmap_card)

        # 4. Habit Consistency Leaderboard
        leader_card = QFrame()
        leader_card.setProperty("class", "Card")
        leader_card.setStyleSheet(f"""
            QFrame {{
                background-color: #151824;
                border: 1px solid {BORDER_COLOR};
                border-radius: 12px;
                padding: 18px;
            }}
        """)
        leader_layout = QVBoxLayout(leader_card)
        leader_layout.setSpacing(12)

        leader_header = QLabel("Habit Performance & Streak Rankings")
        leader_header.setStyleSheet(f"font-size: 15px; font-weight: 700; color: {TEXT_PRIMARY};")
        leader_layout.addWidget(leader_header)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            "Habit Name", "Category", "Current Streak", "Best Streak", "30-Day Rate"
        ])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setShowGrid(False)
        self.table.setStyleSheet(f"""
            QTableWidget {{
                background-color: transparent;
                border: none;
                gridline-color: {BORDER_COLOR};
            }}
            QHeaderView::section {{
                background-color: #1A1E2E;
                color: {TEXT_MUTED};
                font-weight: 700;
                font-size: 11px;
                padding: 6px 12px;
                border: none;
                border-bottom: 1px solid {BORDER_COLOR};
            }}
            QTableWidget::item {{
                padding: 8px 12px;
                border-bottom: 1px solid #1E2232;
                color: {TEXT_PRIMARY};
            }}
            QTableWidget::item:selected {{
                background-color: rgba(99, 102, 241, 0.15);
                color: #FFFFFF;
            }}
        """)
        leader_layout.addWidget(self.table)
        main_layout.addWidget(leader_card)

        scroll.setWidget(container)
        outer_layout.addWidget(scroll)

    def refresh_data(self) -> None:
        """Reload habits into selector and refresh analytics data."""
        # Update habit selector combo box
        selected_id = self.habit_selector.currentData()
        self.habit_selector.blockSignals(True)
        self.habit_selector.clear()
        self.habit_selector.addItem("All Habits (Overview)", userData=None)

        habits = self.habit_service.get_active_habits()
        select_idx = 0
        for idx, h in enumerate(habits, start=1):
            self.habit_selector.addItem(f"{h.name} ({h.category})", userData=h.id)
            if h.id == selected_id:
                select_idx = idx

        self.habit_selector.setCurrentIndex(select_idx)
        self.habit_selector.blockSignals(False)

        self._update_analytics(selected_id)

    def _on_habit_selected(self, index: int) -> None:
        habit_id = self.habit_selector.currentData()
        self._update_analytics(habit_id)

    def _update_analytics(self, habit_id: Optional[int]) -> None:
        """Compute metrics and populate heatmap and KPI cards."""
        if habit_id is not None:
            habit = self.habit_service.get_habit(habit_id)
        else:
            habit = None

        # 1. 7-day and 30-day rates
        stats_7d = self.analytics_service.get_completion_stats_for_window(habit, 7)
        stats_30d = self.analytics_service.get_completion_stats_for_window(habit, 30)

        self.card_7d.set_value(f"{stats_7d.rate_percentage}%", f"{stats_7d.total_completed} of {stats_7d.total_scheduled} done")
        self.card_30d.set_value(f"{stats_30d.rate_percentage}%", f"{stats_30d.total_completed} of {stats_30d.total_scheduled} done")

        # 2. Streaks
        if habit is not None:
            streak_info = self.streak_service.calculate_streak(habit)
            curr_str = f"{streak_info.current_streak} Days"
            best_str = f"{streak_info.best_streak} Days"
        else:
            summary = self.analytics_service.get_dashboard_summary()
            curr_str = f"{summary['best_active_streak']} Days"
            # Find best all-time across all habits
            all_habits = self.habit_service.get_active_habits()
            max_best = max((self.streak_service.calculate_streak(h).best_streak for h in all_habits), default=0)
            best_str = f"{max_best} Days"

        self.card_curr_streak.set_value(curr_str)
        self.card_best_streak.set_value(best_str)

        # 3. Activity Grid
        grid_data = self.analytics_service.get_heatmap_grid(habit_id=habit_id, weeks=18)
        self.heatmap_widget.set_data(grid_data)

        # 4. Leaderboard Table
        leaderboard = self.analytics_service.get_habit_leaderboard()
        self.table.setRowCount(len(leaderboard))

        for row_idx, item in enumerate(leaderboard):
            h = item["habit"]
            # Name
            name_item = QTableWidgetItem(h.name)
            self.table.setItem(row_idx, 0, name_item)

            # Category
            cat_item = QTableWidgetItem(h.category)
            self.table.setItem(row_idx, 1, cat_item)

            # Current Streak
            curr_item = QTableWidgetItem(f"🔥 {item['current_streak']} d")
            self.table.setItem(row_idx, 2, curr_item)

            # Best Streak
            best_item = QTableWidgetItem(f"🏆 {item['best_streak']} d")
            self.table.setItem(row_idx, 3, best_item)

            # 30-Day Rate
            rate_item = QTableWidgetItem(f"{item['rate_30d']}%")
            self.table.setItem(row_idx, 4, rate_item)
