"""Main application window with sidebar navigation, view orchestration, and shortcuts."""

from typing import Optional

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QIcon, QKeySequence
from PyQt6.QtWidgets import (
    QButtonGroup,
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from habit_tracker.core.exceptions import HabitTrackerError
from habit_tracker.core.models import Habit
from habit_tracker.services.analytics_service import AnalyticsService
from habit_tracker.services.habit_service import HabitService
from habit_tracker.services.streak_service import StreakService
from habit_tracker.ui.dialogs.habit_dialog import HabitDialog
from habit_tracker.ui.theme import (
    ACCENT_PRIMARY,
    BG_BASE,
    BORDER_COLOR,
    DARK_THEME_QSS,
    TEXT_MUTED,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
)
from habit_tracker.ui.views.analytics_view import AnalyticsView
from habit_tracker.ui.views.dashboard_view import DashboardView
from habit_tracker.ui.views.habits_manage_view import HabitsManageView


class MainWindow(QMainWindow):
    """Primary application window coordinating views and service workflows."""

    def __init__(
        self,
        habit_service: HabitService,
        streak_service: StreakService,
        analytics_service: AnalyticsService,
    ) -> None:
        super().__init__()
        self.habit_service = habit_service
        self.streak_service = streak_service
        self.analytics_service = analytics_service

        self.setWindowTitle("HabitPulse — Desktop Habit Tracker")
        self.resize(1080, 720)
        self.setMinimumSize(880, 600)

        # Apply Global Dark Stylesheet
        self.setStyleSheet(DARK_THEME_QSS)

        self._init_ui()
        self._setup_shortcuts()

    def _init_ui(self) -> None:
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        root_layout = QHBoxLayout(central_widget)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # 1. Left Sidebar
        self.sidebar = QFrame()
        self.sidebar.setObjectName("sidebar")
        self.sidebar.setFixedWidth(220)

        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(14, 20, 14, 20)
        sidebar_layout.setSpacing(6)

        # App Brand Header
        brand_container = QHBoxLayout()
        brand_container.setSpacing(10)

        logo_badge = QLabel("⚡")
        logo_badge.setStyleSheet(f"""
            font-size: 20px;
            background-color: rgba(99, 102, 241, 0.2);
            border-radius: 8px;
            padding: 4px;
        """)
        brand_container.addWidget(logo_badge)

        brand_text_layout = QVBoxLayout()
        brand_text_layout.setSpacing(0)
        brand_title = QLabel("HabitPulse")
        brand_title.setStyleSheet(f"font-size: 16px; font-weight: 800; color: {TEXT_PRIMARY};")
        brand_sub = QLabel("Desktop Tracker")
        brand_sub.setStyleSheet(f"font-size: 11px; color: {TEXT_MUTED};")
        brand_text_layout.addWidget(brand_title)
        brand_text_layout.addWidget(brand_sub)
        brand_container.addLayout(brand_text_layout)
        brand_container.addStretch()

        sidebar_layout.addLayout(brand_container)
        sidebar_layout.addSpacing(20)

        # Nav Buttons
        self.nav_group = QButtonGroup(self)
        self.nav_group.setExclusive(True)

        self.btn_dashboard = QPushButton("  📅  Daily Dashboard")
        self.btn_dashboard.setCheckable(True)
        self.btn_dashboard.setChecked(True)
        self.btn_dashboard.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_dashboard.clicked.connect(lambda: self.switch_view(0))
        self.nav_group.addButton(self.btn_dashboard)
        sidebar_layout.addWidget(self.btn_dashboard)

        self.btn_habits = QPushButton("  📋  Manage Habits")
        self.btn_habits.setCheckable(True)
        self.btn_habits.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_habits.clicked.connect(lambda: self.switch_view(1))
        self.nav_group.addButton(self.btn_habits)
        sidebar_layout.addWidget(self.btn_habits)

        self.btn_analytics = QPushButton("  📈  Analytics & Grid")
        self.btn_analytics.setCheckable(True)
        self.btn_analytics.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_analytics.clicked.connect(lambda: self.switch_view(2))
        self.nav_group.addButton(self.btn_analytics)
        sidebar_layout.addWidget(self.btn_analytics)

        sidebar_layout.addStretch()

        # Quick Add Habit Sidebar Button
        new_habit_sidebar_btn = QPushButton("+ New Habit")
        new_habit_sidebar_btn.setProperty("class", "PrimaryBtn")
        new_habit_sidebar_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        new_habit_sidebar_btn.clicked.connect(self.open_new_habit_dialog)
        sidebar_layout.addWidget(new_habit_sidebar_btn)

        root_layout.addWidget(self.sidebar)

        # 2. Main Content Area (QStackedWidget)
        self.stack = QStackedWidget()

        # View 0: Dashboard
        self.view_dashboard = DashboardView(
            self.habit_service, self.analytics_service, parent=self
        )
        self.view_dashboard.new_habit_requested.connect(self.open_new_habit_dialog)
        self.view_dashboard.edit_habit_requested.connect(self.open_edit_habit_dialog)
        self.view_dashboard.archive_habit_requested.connect(self._on_archive_habit)
        self.view_dashboard.delete_habit_requested.connect(self._on_delete_habit)
        self.view_dashboard.habit_status_changed.connect(self._on_data_modified)
        self.stack.addWidget(self.view_dashboard)

        # View 1: Habits Manage
        self.view_habits = HabitsManageView(
            self.habit_service, self.streak_service, parent=self
        )
        self.view_habits.new_habit_requested.connect(self.open_new_habit_dialog)
        self.view_habits.edit_habit_requested.connect(self.open_edit_habit_dialog)
        self.view_habits.data_changed.connect(self._on_data_modified)
        self.stack.addWidget(self.view_habits)

        # View 2: Analytics
        self.view_analytics = AnalyticsView(
            self.habit_service, self.streak_service, self.analytics_service, parent=self
        )
        self.stack.addWidget(self.view_analytics)

        root_layout.addWidget(self.stack, stretch=1)

        # Status Bar
        status_bar = QStatusBar(self)
        status_bar.setStyleSheet(f"""
            QStatusBar {{
                background-color: #0D0F17;
                color: {TEXT_MUTED};
                font-size: 11px;
                border-top: 1px solid {BORDER_COLOR};
                padding: 2px 12px;
            }}
        """)
        self.setStatusBar(status_bar)
        self.statusBar().showMessage("Ready • Press Ctrl+N to create a new habit", 4000)

    def _setup_shortcuts(self) -> None:
        """Register keyboard shortcuts for fast power-user navigation."""
        # Ctrl+N -> New Habit
        shortcut_new = QAction(self)
        shortcut_new.setShortcut(QKeySequence("Ctrl+N"))
        shortcut_new.triggered.connect(self.open_new_habit_dialog)
        self.addAction(shortcut_new)

        # Ctrl+1 / Ctrl+D -> Dashboard
        shortcut_dash = QAction(self)
        shortcut_dash.setShortcut(QKeySequence("Ctrl+1"))
        shortcut_dash.triggered.connect(lambda: self.switch_view(0))
        self.addAction(shortcut_dash)

        # Ctrl+2 / Ctrl+H -> Manage Habits
        shortcut_habits = QAction(self)
        shortcut_habits.setShortcut(QKeySequence("Ctrl+2"))
        shortcut_habits.triggered.connect(lambda: self.switch_view(1))
        self.addAction(shortcut_habits)

        # Ctrl+3 / Ctrl+A -> Analytics
        shortcut_analytics = QAction(self)
        shortcut_analytics.setShortcut(QKeySequence("Ctrl+3"))
        shortcut_analytics.triggered.connect(lambda: self.switch_view(2))
        self.addAction(shortcut_analytics)

    def switch_view(self, index: int) -> None:
        """Switch current stacked widget page and refresh its data."""
        self.stack.setCurrentIndex(index)
        if index == 0:
            self.btn_dashboard.setChecked(True)
            self.view_dashboard.refresh_data()
        elif index == 1:
            self.btn_habits.setChecked(True)
            self.view_habits.refresh_data()
        elif index == 2:
            self.btn_analytics.setChecked(True)
            self.view_analytics.refresh_data()

    def open_new_habit_dialog(self) -> None:
        """Show habit creation dialog and persist upon acceptance."""
        existing_cats = self.habit_service.get_categories()
        dialog = HabitDialog(habit=None, existing_categories=existing_cats, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted and dialog.result_habit:
            try:
                created = self.habit_service.create_habit(
                    name=dialog.result_habit.name,
                    category=dialog.result_habit.category,
                    description=dialog.result_habit.description,
                    color=dialog.result_habit.color,
                    frequency_type=dialog.result_habit.frequency_type,
                    target_days=dialog.result_habit.target_days,
                )
                self.statusBar().showMessage(f"Created habit '{created.name}' successfully!", 3500)
                self._on_data_modified()
            except HabitTrackerError as e:
                QMessageBox.critical(self, "Creation Error", str(e))

    def open_edit_habit_dialog(self, habit_id: int) -> None:
        """Show habit edit dialog and persist changes."""
        habit = self.habit_service.get_habit(habit_id)
        if not habit:
            return

        existing_cats = self.habit_service.get_categories()
        dialog = HabitDialog(habit=habit, existing_categories=existing_cats, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted and dialog.result_habit:
            try:
                updated = self.habit_service.update_habit(
                    habit_id=habit_id,
                    name=dialog.result_habit.name,
                    category=dialog.result_habit.category,
                    description=dialog.result_habit.description,
                    color=dialog.result_habit.color,
                    frequency_type=dialog.result_habit.frequency_type,
                    target_days=dialog.result_habit.target_days,
                )
                self.statusBar().showMessage(f"Updated habit '{updated.name}'!", 3500)
                self._on_data_modified()
            except HabitTrackerError as e:
                QMessageBox.critical(self, "Update Error", str(e))

    def _on_archive_habit(self, habit_id: int) -> None:
        self.habit_service.archive_habit(habit_id)
        self.statusBar().showMessage("Habit archived.", 3000)
        self._on_data_modified()

    def _on_delete_habit(self, habit_id: int) -> None:
        habit = self.habit_service.get_habit(habit_id)
        if not habit:
            return

        reply = QMessageBox.question(
            self,
            "Delete Habit",
            f"Permanently delete habit '{habit.name}' and all its logs?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.habit_service.delete_habit(habit_id)
            self.statusBar().showMessage("Habit deleted.", 3000)
            self._on_data_modified()

    def _on_data_modified(self) -> None:
        """Notify active views to reload data."""
        current_idx = self.stack.currentIndex()
        if current_idx == 0:
            self.view_dashboard.refresh_data()
        elif current_idx == 1:
            self.view_habits.refresh_data()
        elif current_idx == 2:
            self.view_analytics.refresh_data()
