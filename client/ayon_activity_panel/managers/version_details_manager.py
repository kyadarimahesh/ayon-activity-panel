"""Version details UI manager."""


class VersionDetailsManager:
    """Manages version details UI components."""

    def __init__(self, ui, parent):
        self.ui = ui
        self.parent = parent

    def update(self, row_data, available_statuses):
        """Update version details UI."""
        path = row_data.get('path', 'N/A')
        author = row_data.get('author', 'N/A')

        self.ui.pathLabel_value.setText(path)
        self._update_version_combo(row_data)
        self._update_status_combo(row_data, available_statuses)
        self.ui.authorLineEdit.setText(author)

    def _update_version_combo(self, row_data):
        versions = row_data.get('versions', [])
        current_version = row_data.get('current_version', '')

        self.ui.versionComboBox.blockSignals(True)
        self.ui.versionComboBox.clear()
        if versions:
            self.ui.versionComboBox.addItems(versions)
            if current_version in versions:
                self.ui.versionComboBox.setCurrentText(current_version)
                print(f"      ✅ Set to: {current_version}")
        self.ui.versionComboBox.blockSignals(False)

    def _update_status_combo(self, row_data, available_statuses):
        current_status = row_data.get('version_status', 'N/A')

        self.ui.statusComboBox.blockSignals(True)
        self.ui.statusComboBox.clear()

        if available_statuses:
            for status_item in available_statuses:
                if status_item.get('value') != 'All':
                    self.ui.statusComboBox.addItem(status_item.get('value', ''))

        if current_status != 'N/A':
            index = self.ui.statusComboBox.findText(current_status)
            if index >= 0:
                self.ui.statusComboBox.setCurrentIndex(index)

        self.ui.statusComboBox.blockSignals(False)

    def clear(self):
        """Clear all version details."""
        self.ui.pathLabel_value.setText("")
        self.ui.versionComboBox.clear()
        self.ui.statusComboBox.clear()
        self.ui.authorLineEdit.clear()
