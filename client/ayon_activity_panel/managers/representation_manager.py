"""Representation manager for RV integration."""

from qtpy.QtCore import Qt
from qtpy.QtWidgets import QLabel, QPushButton, QMessageBox, QSpacerItem, QSizePolicy

from pathlib import Path
import os
import re


class RepresentationManager:
    """Manages representation switching in RV."""

    def __init__(self, ui, parent):
        self.ui = ui
        self.parent = parent
        self.loaded_representations = {}

    def update_tab(self, row_data):
        """Update representations tab UI."""

        rep_layout = self.ui.representationsTabLayout

        while rep_layout.count() > 0:
            item = rep_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not row_data:
            print(f"   ⚠️ No row_data provided")
            return

        representations = row_data.get('representations', [])
        current_rep_path = row_data.get('current_representation_path', '')

        if not representations:
            no_rep_label = QLabel("No representations available")
            no_rep_label.setAlignment(Qt.AlignCenter)
            rep_layout.addWidget(no_rep_label)
        else:
            rep_by_ext = self._group_by_extension(representations)
            self._create_buttons(rep_by_ext, current_rep_path, rep_layout)

        rep_layout.addItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))

    def _group_by_extension(self, representations):
        rep_by_ext = {}
        for rep in representations:
            path = rep.get('path', '')
            if path:
                ext = Path(path).suffix.lower()
                if ext not in rep_by_ext:
                    rep_by_ext[ext] = []
                rep_by_ext[ext].append(rep)
        return rep_by_ext

    def _create_buttons(self, rep_by_ext, current_rep_path, layout):
        for ext, reps in rep_by_ext.items():
            button = QPushButton(ext or "unknown")
            button.setCheckable(True)

            is_current = any(
                Path(rep.get('path', '')).suffix.lower() == Path(current_rep_path).suffix.lower()
                for rep in reps
            ) if current_rep_path else False

            if is_current:
                button.setChecked(True)
                button.setStyleSheet("""
                    QPushButton {
                        background-color: #4CAF50;
                        color: white;
                        font-weight: bold;
                        border: 2px solid #45a049;
                    }
                """)

            button.clicked.connect(lambda checked=False, r=reps: self.switch_representation(r))
            layout.addWidget(button)

    def switch_representation(self, representations):
        """Switch to a different representation in RV."""

        if not representations:
            print(f"   ⚠️ No representations provided")
            return

        new_rep = representations[0]
        new_path = new_rep.get('path', '')

        if not new_path:
            QMessageBox.warning(self.parent, "Error", "No valid path.")
            return

        try:
            import rv.commands as commands

            norm_path = Path(new_path).as_posix()

            if norm_path in self.loaded_representations:
                print(f"   🔁 Switching to already loaded representation")
                self._switch_to_loaded(norm_path, new_path, commands)
            else:
                print(f"   🎬 Loading new representation in RV")
                self._load_new_representation(new_path, norm_path, commands)

        except Exception as e:
            print(f"   ❌ Error: {e}")
            QMessageBox.critical(self.parent, "Error", str(e))

    def _switch_to_loaded(self, norm_path, new_path, commands):
        source_group = self.loaded_representations[norm_path]
        if source_group and commands.nodeExists(source_group):
            commands.setViewNode(source_group)
            self.parent.current_version_data['current_representation_path'] = new_path

            # Trigger activity panel update when switching
            if hasattr(self.parent, 'rv_integration') and self.parent.rv_integration:
                self.parent.rv_integration._debounced_update()

            self.update_tab(self.parent.current_version_data)
        else:
            del self.loaded_representations[norm_path]
            self.switch_representation([{'path': new_path}])

    def _load_new_representation(self, new_path, norm_path, commands):
        ext = Path(new_path).suffix.lower()
        if ext in ['.exr', '.jpg', '.jpeg', '.png', '.tiff', '.dpx']:
            load_path = self._get_sequence_pattern(new_path)
        else:
            load_path = new_path

        loaded_nodes = commands.addSourcesVerbose([[load_path]])

        if loaded_nodes:
            source_node = loaded_nodes[0]
            source_group = commands.nodeGroup(source_node)
            self.loaded_representations[norm_path] = source_group
            commands.setViewNode(source_group)
            self.parent.current_version_data['current_representation_path'] = new_path

            # Store metadata on node
            self._store_representation_metadata(source_node, self.parent.current_version_data)

            self.update_tab(self.parent.current_version_data)
        else:
            QMessageBox.warning(self.parent, "Error", "Failed to load.")

    @staticmethod
    def _store_representation_metadata(node, version_data):
        """Store version metadata on representation node."""
        try:
            import rv.commands as commands
            import json

            metadata = {
                'version_id': version_data.get('version_id'),
                'version_name': version_data.get('current_version'),
                'version_status': version_data.get('version_status'),
                'author': version_data.get('author'),
                'product_name': version_data.get('product_name'),
                'folder_path': version_data.get('path'),
                'file_path': version_data.get('current_representation_path'),
                'versions': json.dumps(version_data.get('versions', [])),
                'all_product_versions': json.dumps(version_data.get('all_product_versions', [])),
                'representations': json.dumps(version_data.get('representations', []))
            }

            for key, value in metadata.items():
                if value:
                    prop = f"{node}.ayon.{key}"
                    if not commands.propertyExists(prop):
                        commands.newProperty(prop, commands.StringType, 1)
                    commands.setStringProperty(prop, [value], True)

        except Exception as e:
            print(f"❌ [REP MANAGER] Error storing metadata: {e}")
            import traceback
            traceback.print_exc()

    def _get_sequence_pattern(self, path):
        folder = os.path.dirname(path)
        filename = os.path.basename(path)

        match = re.match(r"^(.*?)(\d+)(\.[^.]+)$", filename)
        if not match:
            return path

        prefix, frame_str, ext = match.groups()

        frames = []
        for f in os.listdir(folder):
            m = re.match(rf"^{re.escape(prefix)}(\d+){re.escape(ext)}$", f)
            if m:
                frames.append(int(m.group(1)))

        if not frames:
            return path

        start, end = min(frames), max(frames)
        return os.path.join(folder, f"{prefix}{start}-{end}#{ext}")
