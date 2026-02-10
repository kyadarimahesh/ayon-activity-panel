"""Annotations dialog for navigating through activity thumbnails."""

import base64

from qtpy.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QWidget
)
from qtpy.QtCore import Qt
from qtpy.QtGui import QPixmap, QKeyEvent
from ayon_core import style


class AnnotationsDialog(QDialog):
    """Dialog for viewing and navigating through multiple annotations."""

    def __init__(self, images, current_index=0, parent=None):
        """Initialize annotations dialog.
        
        Args:
            images: List of tuples (file_id, filename, image_data_base64)
            current_index: Index of annotation to show initially
            parent: Parent widget
        """
        super().__init__(parent)
        self.images = images
        self.current_index = current_index

        self.setWindowTitle("Annotations")
        self.setModal(True)
        self.resize(900, 700)
        self.setStyleSheet(style.load_stylesheet())

        self._setup_ui()
        self._show_current_image()

    def _setup_ui(self):
        """Setup UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        # Image display area
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setMinimumSize(800, 600)
        layout.addWidget(self.image_label)

        # Navigation controls
        nav_layout = QHBoxLayout()
        nav_layout.setSpacing(5)

        # Previous button
        self.prev_btn = QPushButton("◀" if hasattr(Qt, "AA_EnableHighDpiScaling") else "<")
        self.prev_btn.setFixedWidth(40)
        self.prev_btn.clicked.connect(self._show_previous)
        self.prev_btn.setEnabled(len(self.images) > 1)
        nav_layout.addWidget(self.prev_btn)

        # Counter and filename label
        info_widget = QWidget()
        info_layout = QVBoxLayout(info_widget)
        info_layout.setContentsMargins(0, 0, 0, 0)
        info_layout.setSpacing(2)

        self.counter_label = QLabel()
        self.counter_label.setAlignment(Qt.AlignCenter)
        info_layout.addWidget(self.counter_label)

        self.filename_label = QLabel()
        self.filename_label.setAlignment(Qt.AlignCenter)
        self.filename_label.setStyleSheet("color: #9aa4ad; font-size: 10px;")
        info_layout.addWidget(self.filename_label)

        nav_layout.addWidget(info_widget, 1)

        # Next button
        self.next_btn = QPushButton("▶" if hasattr(Qt, "AA_EnableHighDpiScaling") else ">")
        self.next_btn.setFixedWidth(40)
        self.next_btn.clicked.connect(self._show_next)
        self.next_btn.setEnabled(len(self.images) > 1)
        nav_layout.addWidget(self.next_btn)

        layout.addLayout(nav_layout)

    def _show_current_image(self):
        """Display current annotation."""
        if not self.images or self.current_index >= len(self.images):
            return

        file_id, filename, img_data = self.images[self.current_index]

        # Load and display image
        pixmap = QPixmap()
        if pixmap.loadFromData(base64.b64decode(img_data)):
            scaled_pixmap = pixmap.scaled(
                self.image_label.width() - 10,
                self.image_label.height() - 10,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            self.image_label.setPixmap(scaled_pixmap)
        else:
            self.image_label.setText("Failed to load annotation")

        # Update counter
        self.counter_label.setText(f"{self.current_index + 1} / {len(self.images)}")

        # Update filename
        self.filename_label.setText(filename)

        # Update button states
        self.prev_btn.setEnabled(self.current_index > 0)
        self.next_btn.setEnabled(self.current_index < len(self.images) - 1)

    def _show_previous(self):
        """Show previous annotation."""
        if self.current_index > 0:
            self.current_index -= 1
            self._show_current_image()

    def _show_next(self):
        """Show next annotation."""
        if self.current_index < len(self.images) - 1:
            self.current_index += 1
            self._show_current_image()

    def keyPressEvent(self, event: QKeyEvent):
        """Handle keyboard navigation."""
        if event.key() == Qt.Key_Left:
            self._show_previous()
        elif event.key() == Qt.Key_Right:
            self._show_next()
        elif event.key() == Qt.Key_Escape:
            self.accept()
        else:
            super().keyPressEvent(event)
