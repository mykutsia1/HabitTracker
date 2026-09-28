"""Modal dialog for creating and editing habits."""

from typing import List, Optional

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QComboBox,
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QRadioButton,
    QVBoxLayout,
    QWidget,
)

from habit_tracker.core.models import (
    WEEKDAY_NAMES_SHORT,
    FrequencyType,
    Habit,
)
from habit_tracker.ui.theme import (
    ACCENT_PRIMARY,
    BORDER_COLOR,
    DANGER_RED,
    PRESET_COLORS,
    TEXT_MUTED,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
)

DEFAULT_CATEGORIES = [
    "General",
    "Health",
    "Fitness",
    "Learning",
    "Productivity",
    "Mindfulness",
    "Finance",
    "Creative",
]


class ColorSwatchButton(QPushButton):
    """Circular color picker swatch button."""

    def __init__(self, color_hex: str, parent=None) -> None:
        super().__init__(parent)
        self.color_hex = color_hex
        self.setFixedSize(28, 28)
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.update_style(False)

    def update_style(self, is_selected: bool) -> None:
        border = "2px solid #FFFFFF" if is_selected else f"1px solid {BORDER_COLOR}"
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.color_hex};
                border: {border};
                border-radius: 14px;
            }}
        """)


class HabitDialog(QDialog):
    """Dialog for creating a new habit or updating an existing one."""

    def __init__(
        self,
        habit: Optional[Habit] = None,
        existing_categories: Optional[List[str]] = None,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.habit = habit
        self.is_edit = habit is not None

        title = "Edit Habit" if self.is_edit else "Create New Habit"
        self.setWindowTitle(title)
        self.setFixedWidth(460)
        self.setModal(True)

        categories = sorted(list(set(DEFAULT_CATEGORIES + (existing_categories or []))))
        self.available_categories = categories

        self.selected_color = habit.color if (habit and habit.color) else PRESET_COLORS[0]
        self.result_habit: Optional[Habit] = None

        self._init_ui()
        if self.habit:
            self._populate_fields(self.habit)

    def _init_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(16)

        # Header Title
        title_lbl = QLabel(self.windowTitle())
        title_lbl.setStyleSheet(f"font-size: 18px; font-weight: 700; color: {TEXT_PRIMARY};")
        main_layout.addWidget(title_lbl)

        # Error Banner
        self.error_banner = QLabel()
        self.error_banner.setStyleSheet(f"""
            background-color: rgba(239, 68, 68, 0.15);
            color: {DANGER_RED};
            border: 1px solid rgba(239, 68, 68, 0.3);
            border-radius: 6px;
            padding: 8px 12px;
            font-size: 12px;
        """)
        self.error_banner.hide()
        main_layout.addWidget(self.error_banner)

        # 1. Habit Name
        name_group = QVBoxLayout()
        name_group.setSpacing(4)
        name_label = QLabel("HABIT NAME *")
        name_label.setStyleSheet(f"font-size: 11px; font-weight: 700; color: {TEXT_MUTED};")
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("e.g. Morning Workout, Read 20 Pages")
        name_group.addWidget(name_label)
        name_group.addWidget(self.name_input)
        main_layout.addLayout(name_group)

        # 2. Category
        cat_group = QVBoxLayout()
        cat_group.setSpacing(4)
        cat_label = QLabel("CATEGORY / TAG")
        cat_label.setStyleSheet(f"font-size: 11px; font-weight: 700; color: {TEXT_MUTED};")
        self.cat_combo = QComboBox()
        self.cat_combo.setEditable(True)
        self.cat_combo.addItems(self.available_categories)
        cat_group.addWidget(cat_label)
        cat_group.addWidget(self.cat_combo)
        main_layout.addLayout(cat_group)

        # 3. Description / Cue
        desc_group = QVBoxLayout()
        desc_group.setSpacing(4)
        desc_label = QLabel("DESCRIPTION / CUE (OPTIONAL)")
        desc_label.setStyleSheet(f"font-size: 11px; font-weight: 700; color: {TEXT_MUTED};")
        self.desc_input = QLineEdit()
        self.desc_input.setPlaceholderText("e.g. Right after morning coffee")
        desc_group.addWidget(desc_label)
        desc_group.addWidget(self.desc_input)
        main_layout.addLayout(desc_group)

        # 4. Color Picker
        color_group = QVBoxLayout()
        color_group.setSpacing(6)
        color_label = QLabel("ACCENT COLOR")
        color_label.setStyleSheet(f"font-size: 11px; font-weight: 700; color: {TEXT_MUTED};")
        color_group.addWidget(color_label)

        color_row = QHBoxLayout()
        color_row.setSpacing(8)
        self.color_buttons: List[ColorSwatchButton] = []
        self.color_button_group = QButtonGroup(self)
        self.color_button_group.setExclusive(True)

        for c_hex in PRESET_COLORS:
            swatch = ColorSwatchButton(c_hex)
            if c_hex.lower() == self.selected_color.lower():
                swatch.setChecked(True)
                swatch.update_style(True)
            swatch.clicked.connect(self._create_color_handler(swatch, c_hex))
            self.color_button_group.addButton(swatch)
            self.color_buttons.append(swatch)
            color_row.addWidget(swatch)

        color_row.addStretch()
        color_group.addLayout(color_row)
        main_layout.addLayout(color_group)

        # 5. Frequency Type
        freq_group = QVBoxLayout()
        freq_group.setSpacing(6)
        freq_label = QLabel("FREQUENCY")
        freq_label.setStyleSheet(f"font-size: 11px; font-weight: 700; color: {TEXT_MUTED};")
        freq_group.addWidget(freq_label)

        self.radio_daily = QRadioButton("Daily (Every day)")
        self.radio_weekdays = QRadioButton("Weekdays (Mon – Fri)")
        self.radio_custom = QRadioButton("Specific Days of Week")
        self.radio_daily.setChecked(True)

        freq_radio_layout = QHBoxLayout()
        freq_radio_layout.addWidget(self.radio_daily)
        freq_radio_layout.addWidget(self.radio_weekdays)
        freq_radio_layout.addWidget(self.radio_custom)
        freq_group.addLayout(freq_radio_layout)

        # Custom Days Checkboxes Container
        self.custom_days_widget = QWidget()
        custom_layout = QHBoxLayout(self.custom_days_widget)
        custom_layout.setContentsMargins(0, 4, 0, 4)
        custom_layout.setSpacing(6)

        self.day_checkboxes: List[QCheckBox] = []
        for idx, day_name in enumerate(WEEKDAY_NAMES_SHORT):
            cb = QCheckBox(day_name)
            cb.setChecked(True)
            self.day_checkboxes.append(cb)
            custom_layout.addWidget(cb)

        self.custom_days_widget.hide()
        freq_group.addWidget(self.custom_days_widget)

        self.radio_daily.toggled.connect(self._on_freq_changed)
        self.radio_weekdays.toggled.connect(self._on_freq_changed)
        self.radio_custom.toggled.connect(self._on_freq_changed)

        main_layout.addLayout(freq_group)

        # Action Buttons
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)
        btn_row.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setProperty("class", "SecondaryBtn")
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(cancel_btn)

        save_btn = QPushButton("Save Habit" if self.is_edit else "Create Habit")
        save_btn.setProperty("class", "PrimaryBtn")
        save_btn.clicked.connect(self._on_save)
        btn_row.addWidget(save_btn)

        main_layout.addSpacing(8)
        main_layout.addLayout(btn_row)

    def _create_color_handler(self, swatch: ColorSwatchButton, hex_val: str):
        def handler():
            self.selected_color = hex_val
            for b in self.color_buttons:
                b.update_style(b == swatch)
        return handler

    def _on_freq_changed(self) -> None:
        self.custom_days_widget.setVisible(self.radio_custom.isChecked())

    def _populate_fields(self, habit: Habit) -> None:
        self.name_input.setText(habit.name)
        self.desc_input.setText(habit.description)

        idx = self.cat_combo.findText(habit.category)
        if idx >= 0:
            self.cat_combo.setCurrentIndex(idx)
        else:
            self.cat_combo.setCurrentText(habit.category)

        self.selected_color = habit.color
        for b in self.color_buttons:
            is_match = (b.color_hex.lower() == habit.color.lower())
            b.setChecked(is_match)
            b.update_style(is_match)

        if habit.frequency_type == FrequencyType.DAILY:
            self.radio_daily.setChecked(True)
        elif habit.frequency_type == FrequencyType.WEEKDAYS:
            self.radio_weekdays.setChecked(True)
        elif habit.frequency_type == FrequencyType.CUSTOM:
            self.radio_custom.setChecked(True)
            self.custom_days_widget.show()
            for day_idx, cb in enumerate(self.day_checkboxes):
                cb.setChecked(day_idx in habit.target_days)

    def _on_save(self) -> None:
        name = self.name_input.text().strip()
        if not name:
            self.error_banner.setText("Please enter a habit name.")
            self.error_banner.show()
            return

        category = self.cat_combo.currentText().strip() or "General"
        description = self.desc_input.text().strip()

        if self.radio_daily.isChecked():
            freq_type = FrequencyType.DAILY
            target_days = [0, 1, 2, 3, 4, 5, 6]
        elif self.radio_weekdays.isChecked():
            freq_type = FrequencyType.WEEKDAYS
            target_days = [0, 1, 2, 3, 4]
        else:
            freq_type = FrequencyType.CUSTOM
            target_days = [i for i, cb in enumerate(self.day_checkboxes) if cb.isChecked()]
            if not target_days:
                self.error_banner.setText("Please select at least one day for custom frequency.")
                self.error_banner.show()
                return

        habit_id = self.habit.id if self.habit else None
        archived = self.habit.archived if self.habit else False

        self.result_habit = Habit(
            id=habit_id,
            name=name,
            category=category,
            description=description,
            color=self.selected_color,
            frequency_type=freq_type,
            target_days=target_days,
            archived=archived,
        )
        self.accept()
