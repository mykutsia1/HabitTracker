"""GitHub-style activity heat-grid component for visual habit tracking analytics."""

from datetime import date
from typing import List, Optional

from PyQt6.QtCore import QPoint, QRectF, Qt
from PyQt6.QtGui import QColor, QFont, QMouseEvent, QPainter, QPen
from PyQt6.QtWidgets import QToolTip, QWidget

from habit_tracker.core.models import HeatmapCell
from habit_tracker.ui.theme import (
    HEATMAP_COLORS,
    TEXT_MUTED,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
)

WEEKDAY_LABELS = ["Mon", "", "Wed", "", "Fri", "", ""]


class HeatmapWidget(QWidget):
    """Custom painted GitHub-style contribution heat-grid widget."""

    def __init__(
        self,
        grid_data: Optional[List[List[HeatmapCell]]] = None,
        cell_size: int = 14,
        cell_spacing: int = 4,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.grid_data = grid_data or []
        self.cell_size = cell_size
        self.cell_spacing = cell_spacing

        # Margins for labels
        self.left_margin = 36   # space for "Mon", "Wed", "Fri" labels
        self.top_margin = 24    # space for month names ("Jan", "Feb"...)
        self.bottom_margin = 28 # space for legend

        self.hovered_cell: Optional[HeatmapCell] = None
        self.setMouseTracking(True)
        self.update_geometry()

    def set_data(self, grid_data: List[List[HeatmapCell]]) -> None:
        """Update grid data and trigger repaint."""
        self.grid_data = grid_data
        self.update_geometry()
        self.update()

    def update_geometry(self) -> None:
        """Recalculate minimum widget size based on grid dimensions."""
        if not self.grid_data or not self.grid_data[0]:
            self.setMinimumSize(400, 160)
            return

        num_cols = len(self.grid_data[0])
        total_width = self.left_margin + (num_cols * (self.cell_size + self.cell_spacing)) + 16
        total_height = self.top_margin + (7 * (self.cell_size + self.cell_spacing)) + self.bottom_margin
        self.setMinimumSize(int(total_width), int(total_height))

    def _get_cell_rect(self, row: int, col: int) -> QRectF:
        """Calculate QRectF for cell at (row, col)."""
        x = self.left_margin + col * (self.cell_size + self.cell_spacing)
        y = self.top_margin + row * (self.cell_size + self.cell_spacing)
        return QRectF(x, y, self.cell_size, self.cell_size)

    def paintEvent(self, event) -> None:
        """Render heatmap tiles, month labels, weekday labels, and legend."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        font = QFont()
        font.setPointSize(9)
        font.setWeight(QFont.Weight.Medium)
        painter.setFont(font)

        if not self.grid_data or not self.grid_data[0]:
            painter.setPen(QColor(TEXT_MUTED))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "No activity data available yet.")
            return

        num_rows = len(self.grid_data)  # 7
        num_cols = len(self.grid_data[0])

        # 1. Draw Weekday Labels (Mon, Wed, Fri)
        painter.setPen(QColor(TEXT_MUTED))
        for row in range(num_rows):
            label = WEEKDAY_LABELS[row]
            if label:
                y = self.top_margin + row * (self.cell_size + self.cell_spacing) + (self.cell_size * 0.8)
                painter.drawText(0, int(y), self.left_margin - 8, self.cell_size, Qt.AlignmentFlag.AlignRight, label)

        # 2. Draw Month Labels along Top
        last_month = None
        for col in range(num_cols):
            cell = self.grid_data[0][col]
            if cell:
                month_num = cell.date.month
                if month_num != last_month:
                    month_name = cell.date.strftime("%b")
                    x = self.left_margin + col * (self.cell_size + self.cell_spacing)
                    painter.drawText(int(x), 16, month_name)
                    last_month = month_num

        # 3. Draw Grid Cells
        no_pen = QPen(Qt.PenStyle.NoPen)
        hover_pen = QPen(QColor("#FFFFFF"), 1.5)

        for row in range(num_rows):
            for col in range(num_cols):
                cell = self.grid_data[row][col]
                rect = self._get_cell_rect(row, col)

                color_hex = HEATMAP_COLORS[cell.intensity]
                painter.setBrush(QColor(color_hex))

                if self.hovered_cell == cell:
                    painter.setPen(hover_pen)
                else:
                    painter.setPen(no_pen)

                painter.drawRoundedRect(rect, 3.0, 3.0)

        # 4. Draw Legend (Bottom Right)
        legend_y = self.top_margin + (7 * (self.cell_size + self.cell_spacing)) + 12
        legend_start_x = self.width() - 170

        painter.setPen(QColor(TEXT_MUTED))
        painter.drawText(int(legend_start_x - 32), int(legend_y + 10), "Less")

        curr_lx = legend_start_x
        painter.setPen(no_pen)
        for c_hex in HEATMAP_COLORS:
            painter.setBrush(QColor(c_hex))
            painter.drawRoundedRect(QRectF(curr_lx, legend_y, 11, 11), 2.0, 2.0)
            curr_lx += 15

        painter.setPen(QColor(TEXT_MUTED))
        painter.drawText(int(curr_lx + 4), int(legend_y + 10), "More")

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        """Detect cell under cursor and display informative tooltip."""
        if not self.grid_data or not self.grid_data[0]:
            return

        pos = event.position()
        found_cell: Optional[HeatmapCell] = None

        num_rows = len(self.grid_data)
        num_cols = len(self.grid_data[0])

        for row in range(num_rows):
            for col in range(num_cols):
                rect = self._get_cell_rect(row, col)
                if rect.contains(pos):
                    found_cell = self.grid_data[row][col]
                    break
            if found_cell:
                break

        if found_cell != self.hovered_cell:
            self.hovered_cell = found_cell
            self.update()

            if found_cell:
                formatted_date = found_cell.date.strftime("%A, %b %d, %Y")
                if found_cell.scheduled_count == 0:
                    text = f"<b>{formatted_date}</b><br/>No habits scheduled"
                else:
                    pct = found_cell.rate_percentage
                    text = (
                        f"<b>{formatted_date}</b><br/>"
                        f"{found_cell.completed_count} of {found_cell.scheduled_count} completed ({pct}%)"
                    )
                QToolTip.showText(event.globalPosition().toPoint(), text, self)
            else:
                QToolTip.hideText()

        super().mouseMoveEvent(event)

    def leaveEvent(self, event) -> None:
        """Clear hover state when mouse leaves the heatmap area."""
        self.hovered_cell = None
        self.update()
        super().leaveEvent(event)
