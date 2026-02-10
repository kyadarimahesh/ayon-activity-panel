"""Version details UI manager."""
from __future__ import annotations

from typing import TYPE_CHECKING, Optional, Any

from ayon_core.lib import Logger

if TYPE_CHECKING:
    from qtpy import QtWidgets

log = Logger.get_logger(__name__)


class VersionDetailsManager:
    """Manages version details UI components."""

    def __init__(self, ui: Any, parent: QtWidgets.QWidget):
        """Initialize version details manager.
        
        Args:
            ui: UI object with widget references.
            parent: Parent widget.
        """
        self.ui = ui
        self.parent = parent
        self._spacer = None
        self._task_label = None

    def update(
            self,
            version_data: dict[str, Any],
            available_statuses: list[dict[str, Any]],
            dcc_mode: bool = False
    ) -> None:
        """Update version details UI.
        
        Args:
            version_data: Version data dictionary.
            available_statuses: List of available status dictionaries.
            dcc_mode: Whether in DCC mode (task-based) or version mode.
        """
        path = version_data.get('path', 'N/A')
        author = version_data.get('author', 'N/A')

        self.ui.pathLabel_value.setText(path)

        # Handle DCC mode vs Version mode
        if dcc_mode:
            # Show task name instead of version dropdown
            self.ui.versionLabel.setText("Task:")
            self.ui.versionLabel.setVisible(True)
            self.ui.versionComboBox.setVisible(False)

            if self._task_label is None:
                from qtpy.QtWidgets import QLabel
                self._task_label = QLabel()
                self._task_label.setWordWrap(True)
                self.ui.versionGridLayout.addWidget(self._task_label, 1, 1, 1, 1)

            task_name = version_data.get('task_name', 'N/A')
            self._task_label.setText(task_name)
            self._task_label.setVisible(True)

            self.ui.statusLabel.setText("Task status:")
            self.ui.authorLabel.setText("Assignees:")

            if self._spacer is None:
                from qtpy.QtWidgets import QSpacerItem, QSizePolicy
                self._spacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
                self.ui.versionDetailsLayout.addItem(self._spacer)
        else:
            self.ui.versionLabel.setText("Version:")
            self.ui.versionLabel.setVisible(True)
            self.ui.versionComboBox.setVisible(True)

            if self._task_label is not None:
                self._task_label.setVisible(False)

            self.ui.statusLabel.setText("Status:")
            self.ui.authorLabel.setText("Author:")
            self._update_version_combo(version_data)

            if self._spacer is not None:
                self.ui.versionDetailsLayout.removeItem(self._spacer)
                self._spacer = None

        self._update_status_combo(version_data, available_statuses)
        self.ui.authorLineEdit.setText(author)

    def _update_version_combo(self, version_data: dict[str, Any]) -> None:
        """Update version combobox.
        
        Args:
            version_data: Version data dictionary.
        """
        versions = version_data.get('versions', [])
        current_version = version_data.get('current_version', '')

        self.ui.versionComboBox.blockSignals(True)
        self.ui.versionComboBox.clear()
        if versions:
            self.ui.versionComboBox.addItems(versions)
            if current_version in versions:
                self.ui.versionComboBox.setCurrentText(current_version)
        self.ui.versionComboBox.blockSignals(False)

    def _update_status_combo(
            self,
            version_data: dict[str, Any],
            available_statuses: list[dict[str, Any]]
    ) -> None:
        """Update status combobox with colored icons matching AYON browser.
        
        Args:
            version_data: Version data dictionary.
            available_statuses: List of available status dictionaries.
        """
        from ayon_core.tools.utils import get_qt_icon

        current_status = version_data.get('version_status', 'N/A')

        self.ui.statusComboBox.blockSignals(True)
        self.ui.statusComboBox.clear()

        if available_statuses:
            for status_item in available_statuses:
                status_name = status_item.get('value', '')
                icon_name = status_item.get('icon', 'circle')
                icon_color = status_item.get('color', '#FFFFFF')

                icon_def = {
                    "type": "material-symbols",
                    "name": icon_name,
                    "color": icon_color,
                }
                icon = get_qt_icon(icon_def)
                self.ui.statusComboBox.addItem(icon, status_name)

        if current_status != 'N/A':
            index = self.ui.statusComboBox.findText(current_status)
            if index >= 0:
                self.ui.statusComboBox.setCurrentIndex(index)

        self.ui.statusComboBox.blockSignals(False)

        # Disable scroll wheel to prevent accidental status changes
        self.ui.statusComboBox.wheelEvent = lambda event: None

    def clear(self) -> None:
        """Clear all version details."""
        self.ui.pathLabel_value.setText("")
        self.ui.versionComboBox.clear()
        self.ui.statusComboBox.clear()
        self.ui.authorLineEdit.clear()
