"""Main window for Snipping Tool."""
from qtpy import QtWidgets, QtCore, QtGui

from ayon_core import style
from ayon_core.lib import Logger

from .snipping_widget import SnippingWidget

log = Logger.get_logger(__name__)


class SnippingTool(QtWidgets.QMainWindow):
    """Main Snipping Tool window."""

    def __init__(self, parent=None):
        super(SnippingTool, self).__init__(parent)

        self.setWindowTitle("Snipping Tool")
        self.setGeometry(100, 100, 400, 300)
        self.setStyleSheet(style.load_stylesheet())

        self.current_image = None
        self.snipping_widget = None

        self._setup_ui()

    def _setup_ui(self):
        """Set up the user interface."""
        central_widget = QtWidgets.QWidget(self)
        self.setCentralWidget(central_widget)

        main_layout = QtWidgets.QVBoxLayout(central_widget)
        main_layout.setContentsMargins(5, 5, 5, 5)

        self._create_toolbar()
        self._create_image_display(main_layout)
        self._create_menubar()

        self.statusBar().showMessage("Ready")

    def _create_toolbar(self):
        """Create toolbar with actions."""
        toolbar = QtWidgets.QToolBar(self)
        self.addToolBar(toolbar)

        new_action = QtWidgets.QAction("New", self)
        new_action.setShortcut("Ctrl+N")
        new_action.triggered.connect(self.start_snipping)
        toolbar.addAction(new_action)

        save_action = QtWidgets.QAction("Save", self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self.save_image)
        toolbar.addAction(save_action)

        copy_action = QtWidgets.QAction("Copy", self)
        copy_action.setShortcut("Ctrl+C")
        copy_action.triggered.connect(self.copy_to_clipboard)
        toolbar.addAction(copy_action)

        toolbar.addSeparator()

        clear_action = QtWidgets.QAction("Clear", self)
        clear_action.triggered.connect(self.clear_image)
        toolbar.addAction(clear_action)

        self._toolbar = toolbar
        self._new_action = new_action
        self._save_action = save_action
        self._copy_action = copy_action
        self._clear_action = clear_action

    def _create_image_display(self, layout):
        """Create image display area."""
        self.image_label = QtWidgets.QLabel(self)
        self.image_label.setAlignment(QtCore.Qt.AlignCenter)
        self.image_label.setMinimumSize(300, 200)
        self.image_label.setText("Click 'New' to capture a screenshot")

        scroll_area = QtWidgets.QScrollArea(self)
        scroll_area.setWidget(self.image_label)
        scroll_area.setWidgetResizable(True)
        layout.addWidget(scroll_area)

    def _create_menubar(self):
        """Create menu bar."""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("&File")
        file_menu.addAction(self._new_action)
        file_menu.addAction(self._save_action)
        file_menu.addSeparator()

        exit_action = QtWidgets.QAction("E&xit", self)
        exit_action.setShortcut("Alt+F4")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Edit menu
        edit_menu = menubar.addMenu("&Edit")
        edit_menu.addAction(self._copy_action)
        edit_menu.addAction(self._clear_action)

        # Help menu
        help_menu = menubar.addMenu("&Help")
        about_action = QtWidgets.QAction("&About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def start_snipping(self):
        """Start the snipping process."""
        self.hide()
        QtCore.QTimer.singleShot(200, self._show_snipping_widget)

    def _show_snipping_widget(self):
        """Show the snipping widget."""
        self.snipping_widget = SnippingWidget()
        self.snipping_widget.closed.connect(self._on_snipping_closed)

    def _on_snipping_closed(self):
        """Handle snipping widget closed."""
        if self.snipping_widget:
            captured = self.snipping_widget.get_captured_image()
            if captured and not captured.isNull():
                self.current_image = captured
                self.display_image(captured)
                self.statusBar().showMessage(
                    "Captured: {} x {}".format(
                        captured.width(), captured.height()
                    )
                )
            else:
                self.statusBar().showMessage("Capture cancelled")
            self.snipping_widget = None
        self.show()
        self.activateWindow()

    def display_image(self, pixmap):
        """Display the captured image."""
        if pixmap and not pixmap.isNull():
            scaled_pixmap = pixmap.scaled(
                800, 600,
                QtCore.Qt.KeepAspectRatio,
                QtCore.Qt.SmoothTransformation
            )
            self.image_label.setPixmap(scaled_pixmap)
            self.image_label.setMinimumSize(scaled_pixmap.size())

    def save_image(self):
        """Save the current image to file."""
        if not self.current_image or self.current_image.isNull():
            QtWidgets.QMessageBox.warning(
                self, "No Image",
                "No image to save. Please capture a screenshot first."
            )
            return

        file_path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "Save Image", "",
            "PNG Files (*.png);;JPEG Files (*.jpg *.jpeg);;All Files (*.*)"
        )

        if file_path:
            if self.current_image.save(file_path):
                self.statusBar().showMessage(
                    "Saved to {}".format(file_path)
                )
                QtWidgets.QMessageBox.information(
                    self, "Success",
                    "Image saved successfully to:\n{}".format(file_path)
                )
            else:
                QtWidgets.QMessageBox.critical(
                    self, "Error", "Failed to save image."
                )

    def copy_to_clipboard(self):
        """Copy the current image to clipboard."""
        if not self.current_image or self.current_image.isNull():
            QtWidgets.QMessageBox.warning(
                self, "No Image",
                "No image to copy. Please capture a screenshot first."
            )
            return

        clipboard = QtWidgets.QApplication.clipboard()
        clipboard.setPixmap(self.current_image)
        self.statusBar().showMessage("Image copied to clipboard")

    def clear_image(self):
        """Clear the current image."""
        self.current_image = None
        self.image_label.clear()
        self.image_label.setText("Click 'New' to capture a screenshot")
        self.statusBar().showMessage("Image cleared")

    def show_about(self):
        """Show about dialog."""
        QtWidgets.QMessageBox.about(
            self, "About Snipping Tool",
            "<h3>Snipping Tool</h3>"
            "<p>Screen capture tool with AYON styling.</p>"
            "<p><b>Shortcuts:</b> Ctrl+N: New | Ctrl+S: Save | "
            "Ctrl+C: Copy | ESC: Cancel</p>"
        )
