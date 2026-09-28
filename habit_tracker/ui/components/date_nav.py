"""Date navigation controls and calendar picker for Daily Tracking."""

from datetime import date, timedelta
from typing import Optional

from PyQt6.QtCore import QDate, Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QCalendarWidget,
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from habit_tracker.ui.theme import (
    ACCENT_PRIMARY,
    BORDER_COLOR,
    TEXT_MUTED,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
)


class CalendarPickerModal(QDialog):
    """Clean modal calendar for selecting a specific date."""

    def __init__(self, current_date: date, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Select Date")
        self.setModal(True)
        self.selected_date = current_date

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        self.calendar = QCalendarWidget(self)
        self.calendar.setGridVisible(True)
        self.calendar.setSelectedDate(QDate(current_date.year, current_date.month, current_date.day))
        self.calendar.setStyleSheet(f"""
            QCalendarWidget QWidget {{
                background-color: #171922;
                color: {TEXT_PRIMARY};
            }}
            QCalendarWidget QToolButton {{
                color: {TEXT_PRIMARY};
                background-color: transparent;
                border-radius: 4px;
                padding: 4px;
            }}
            QCalendarWidget QMenu {{
                background-color: #23283B;
                color: {TEXT_PRIMARY};
            }}
            QCalendarWidget QAbstractItemView:enabled {{
                selection-background-color: {ACCENT_PRIMARY};
                selection-color: white;
            }}
        """)
        layout.addWidget(self.calendar)

        btn_row = QHBoxLayout()
        btn_row.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setProperty("class", "SecondaryBtn")
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(cancel_btn)

        confirm_btn = QPushButton("Select")
        confirm_btn.setProperty("class", "PrimaryBtn")
        confirm_btn.clicked.connect(self._on_confirm)
        btn_row.addWidget(confirm_btn)

        layout.addLayout(btn_row)

    def _on_confirm(self) -> None:
        qdate = self.calendar.selectedDate()
        self.selected_date = date(qdate.year(), qdate.month(), qdate.day())
        self.accept()


class DateNavigator(QWidget):
    """Top bar for navigating days with previous/next buttons and calendar jump."""

    date_changed = pyqtSignal(date)

    def __init__(self, initial_date: Optional[date] = None, parent=None) -> None:
        super().__init__(parent)
        self.current_date = initial_date or date.today()

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # Previous Day button
        self.prev_btn = QPushButton("◀")
        self.prev_btn.setToolTip("Previous Day")
        self.prev_btn.setFixedSize(36, 36)
        self.prev_btn.setProperty("class", "SecondaryBtn")
        self.prev_btn.clicked.connect(self._go_previous_day)
        layout.addWidget(self.prev_btn)

        # Date Label
        self.date_label = QLabel()
        self.date_label.setStyleSheet(f"""
            font-size: 16px;
            font-weight: 700;
            color: {TEXT_PRIMARY};
            padding: 4px 10px;
        """)
        self.date_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.date_label)

        # Next Day button
        self.next_btn = QPushButton("▶")
        self.next_btn.setToolTip("Next Day")
        self.next_btn.setFixedSize(36, 36)
        self.next_btn.setProperty("class", "SecondaryBtn")
        self.next_btn.clicked.connect(self._go_next_day)
        layout.addWidget(self.next_btn)

        # Calendar button
        self.calendar_btn = QPushButton("📅 Calendar")
        self.calendar_btn.setFixedHeight(36)
        self.calendar_btn.setProperty("class", "SecondaryBtn")
        self.calendar_btn.clicked.connect(self._open_calendar_picker)
        layout.addWidget(self.calendar_btn)

        # Jump to Today button
        self.today_btn = QPushButton("Today")
        self.today_btn.setFixedHeight(36)
        self.today_btn.setProperty("class", "SecondaryBtn")
        self.today_btn.clicked.connect(self._go_today)
        layout.addWidget(self.today_btn)

        layout.addStretch()

        self._update_display()

    def _update_display(self) -> None:
        today = date.today()
        diff = (self.current_date - today).days

        if diff == 0:
            prefix = "Today, "
        elif diff == -1:
            prefix = "Yesterday, "
        elif diff == 1:
            prefix = "Tomorrow, "
        else:
            prefix = ""

        formatted_str = self.current_date.strftime("%a, %b %d, %Y")
        self.date_label.setText(f"{prefix}{formatted_str}")

        # Enable or highlight today button
        if diff == 0:
            self.today_btn.setStyleSheet(f"border-color: {ACCENT_PRIMARY}; color: {ACCENT_PRIMARY};")
        else:
            self.today_btn.setStyleSheet("")

    def _go_previous_day(self) -> None:
        self.set_date(self.current_date - timedelta(days=1))

    def _go_next_day(self) -> None:
        self.set_date(self.current_date + timedelta(days=1))

    def _go_today(self) -> None:
        self.set_date(date.today())

    def _open_calendar_picker(self) -> None:
        dialog = CalendarPickerModal(self.current_date, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.set_date(dialog.selected_date)

    def set_date(self, new_date: date) -> None:
        """Update current date and emit change signal."""
        if self.current_date != new_date:
            self.current_date = new_date
            self._update_display()
            self.date_changed.emit(self.current_date)
