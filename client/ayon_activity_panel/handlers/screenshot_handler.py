"""Screenshot capture and management handler."""
import os
import tempfile

from qtpy.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QScrollArea, QWidget
from qtpy.QtCore import Qt, QTimer
from qtpy.QtGui import QPixmap

from ayon_core import style
from ayon_core.lib import Logger

log = Logger.get_logger(__name__)


class ScreenshotHandler:
    """Handles screenshot capture, preview, and management."""

    def __init__(self, parent_widget, screenshot_button):
        """Initialize screenshot handler.
        
        Args:
            parent_widget: Parent widget instance
            screenshot_button: Screenshot button widget
        """
        self.parent = parent_widget
        self.screenshot_btn = screenshot_button
        self._pending_screenshots = []
        self.snipping_widget = None

    def launch_capture(self):
        """Launch screenshot capture tool."""
        main_window = self.parent.window()
        if main_window:
            main_window.showMinimized()

        QTimer.singleShot(200, self._show_snipping_widget)

    def _show_snipping_widget(self):
        """Show snipping widget after window is minimized."""
        from ..tools.snipping_tool import SnippingWidget
        self.snipping_widget = SnippingWidget()
        self.snipping_widget.closed.connect(self._on_screenshot_captured)

    def _on_screenshot_captured(self):
        """Handle captured screenshot."""
        if self.snipping_widget and self.snipping_widget.captured_pixmap:
            temp_path = tempfile.mktemp(suffix=".png")
            if self.snipping_widget.captured_pixmap.save(temp_path, "PNG"):
                self._pending_screenshots.append(temp_path)
                self._update_button()
                self._show_preview(self.snipping_widget.captured_pixmap)
                log.info(f"Screenshot attached: {temp_path}")
        else:
            self._restore_window()
        self.snipping_widget = None

    def _show_preview(self, pixmap):
        """Show screenshot preview dialog."""
        dialog = QDialog(self.parent)
        dialog.setWindowTitle("Screenshot Preview")
        dialog.setModal(True)
        dialog.setStyleSheet(style.load_stylesheet())

        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Preview image with border
        img_label = QLabel()
        img_label.setAlignment(Qt.AlignCenter)
        img_label.setStyleSheet(
            "QLabel { "
            "background-color: #2b2b2b; "
            "border: 1px solid #3d3d3d; "
            "padding: 5px; "
            "}"
        )
        scaled = pixmap.scaled(600, 400, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        img_label.setPixmap(scaled)
        img_label.setMinimumSize(620, 420)
        layout.addWidget(img_label)

        # Info label
        count = len(self._pending_screenshots)
        info_label = QLabel("{} screenshot(s) attached".format(count))
        info_label.setAlignment(Qt.AlignCenter)
        info_label.setStyleSheet("color: #9aa4ad; font-size: 11px;")
        layout.addWidget(info_label)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)

        cancel_btn = QPushButton("Cancel All")
        cancel_btn.setFixedHeight(32)
        cancel_btn.clicked.connect(lambda: (self.cancel_all(), self._restore_window(), dialog.accept()))
        btn_layout.addWidget(cancel_btn)

        btn_layout.addStretch()

        add_more_btn = QPushButton("Add More")
        add_more_btn.setFixedHeight(32)
        add_more_btn.clicked.connect(lambda: self._add_more(dialog))
        btn_layout.addWidget(add_more_btn)

        done_btn = QPushButton("Done")
        done_btn.setFixedHeight(32)
        done_btn.setDefault(True)
        done_btn.clicked.connect(lambda: (self._restore_window(), dialog.accept()))
        btn_layout.addWidget(done_btn)

        layout.addLayout(btn_layout)

        dialog.resize(640, 520)
        dialog.exec_()

    def _add_more(self, dialog):
        """Handle add more button click."""
        dialog.accept()
        QTimer.singleShot(300, self.launch_capture)

    def show_all_preview(self):
        """Show preview of all screenshots."""
        if not self._pending_screenshots:
            return

        dialog = QDialog(self.parent)
        dialog.setWindowTitle("All Screenshots")
        dialog.setModal(True)
        dialog.setStyleSheet(style.load_stylesheet())

        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(10, 10, 10, 10)

        # Scroll area for screenshots
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)

        for idx, path in enumerate(self._pending_screenshots):
            pixmap = QPixmap(path)
            if not pixmap.isNull():
                img_label = QLabel()
                img_label.setAlignment(Qt.AlignCenter)
                img_label.setStyleSheet(
                    "QLabel { background-color: #2b2b2b; border: 1px solid #3d3d3d; padding: 5px; margin: 5px; }"
                )
                scaled = pixmap.scaled(500, 300, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                img_label.setPixmap(scaled)
                scroll_layout.addWidget(img_label)

                label = QLabel("Screenshot {}".format(idx + 1))
                label.setAlignment(Qt.AlignCenter)
                label.setStyleSheet("color: #9aa4ad; font-size: 10px;")
                scroll_layout.addWidget(label)

        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)

        # Buttons
        btn_layout = QHBoxLayout()

        cancel_btn = QPushButton("Cancel All")
        cancel_btn.clicked.connect(lambda: (self.cancel_all(), dialog.accept()))
        btn_layout.addWidget(cancel_btn)

        btn_layout.addStretch()

        close_btn = QPushButton("Close")
        close_btn.setDefault(True)
        close_btn.clicked.connect(dialog.accept)
        btn_layout.addWidget(close_btn)

        layout.addLayout(btn_layout)

        dialog.resize(540, 600)
        dialog.exec_()

    def cancel_all(self):
        """Cancel all pending screenshots."""
        for path in self._pending_screenshots:
            try:
                if os.path.exists(path):
                    os.remove(path)
            except Exception as e:
                log.warning(f"Failed to remove temp file {path}: {e}")
        self._pending_screenshots = []
        self._update_button()

    def _update_button(self):
        """Update screenshot button to show count."""
        count = len(self._pending_screenshots)
        if count > 0:
            self.screenshot_btn.setText(f"{count}")
            self.screenshot_btn.setStyleSheet("background-color: rgba(92, 173, 214, .4);")
        else:
            self.screenshot_btn.setText("")
            self.screenshot_btn.setStyleSheet("")

    def _restore_window(self):
        """Restore activity panel window."""
        main_window = self.parent.window()
        if main_window:
            main_window.showNormal()
            main_window.activateWindow()

    def get_screenshot_paths(self):
        """Get list of pending screenshot paths.
        
        Returns:
            list: List of screenshot file paths
        """
        return self._pending_screenshots.copy()

    def clear_screenshots(self):
        """Clear all pending screenshots."""
        self._pending_screenshots = []
        self._update_button()
