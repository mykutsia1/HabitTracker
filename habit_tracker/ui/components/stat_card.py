"""KPI stat summary card component."""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QFrame, QLabel, QVBoxLayout

from habit_tracker.ui.theme import BORDER_COLOR, TEXT_MUTED, TEXT_PRIMARY, TEXT_SECONDARY


class StatCard(QFrame):
    """Modern stat card displaying a single KPI metric."""

    def __init__(
        self,
        title: str,
        value: str = "0",
        subtitle: str = "",
        accent_color: str = "#6366F1",
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.setProperty("class", "Card")
        self.accent_color = accent_color

        self.setStyleSheet(f"""
            StatCard {{
                background-color: #151824;
                border: 1px solid {BORDER_COLOR};
                border-left: 4px solid {accent_color};
                border-radius: 10px;
                padding: 12px;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(4)

        # Title
        self.title_lbl = QLabel(title.upper())
        self.title_lbl.setStyleSheet(f"""
            font-size: 11px;
            font-weight: 700;
            letter-spacing: 0.5px;
            color: {TEXT_MUTED};
        """)
        layout.addWidget(self.title_lbl)

        # Main Value
        self.value_lbl = QLabel(value)
        self.value_lbl.setStyleSheet(f"""
            font-size: 24px;
            font-weight: 700;
            color: {TEXT_PRIMARY};
        """)
        layout.addWidget(self.value_lbl)

        # Subtitle / Hint
        self.sub_lbl = QLabel(subtitle)
        self.sub_lbl.setStyleSheet(f"""
            font-size: 12px;
            color: {TEXT_SECONDARY};
        """)
        if not subtitle:
            self.sub_lbl.hide()
        layout.addWidget(self.sub_lbl)

    def set_value(self, value: str, subtitle: str = "") -> None:
        """Update displayed value and subtitle."""
        self.value_lbl.setText(value)
        if subtitle:
            self.sub_lbl.setText(subtitle)
            self.sub_lbl.show()
        else:
            self.sub_lbl.hide()
