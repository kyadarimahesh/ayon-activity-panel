"""Representation manager for RV integration."""

from qtpy.QtCore import Qt
from qtpy.QtWidgets import QLabel, QPushButton, QSpacerItem, QSizePolicy
from qtmaterialsymbols import get_icon
from ayon_core.tools.utils import show_message_dialog
from pathlib import Path


class RepresentationManager:
    """Manages representation switching in RV."""

    def __init__(self, ui, parent):
        self.ui = ui
        self.parent = parent
        self.loaded_representations = {}

    def update_tab(self, version_data):
        """Update representations tab UI."""
        rep_layout = self.ui.representationsTabLayout
        while rep_layout.count() > 0:
            item = rep_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not version_data:
            return

        representations = version_data.get('representations', [])
        current_rep_path = version_data.get('current_representation_path', '')

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
            button.setIcon(get_icon('movie', color='#99A3B2'))

            is_current = any(
                Path(rep.get('path', '')).suffix.lower() == Path(current_rep_path).suffix.lower()
                for rep in reps
            ) if current_rep_path else False

            if is_current:
                button.setChecked(True)
                button.setStyleSheet("""
                    QPushButton {
                        background-color: rgba(92, 173, 214, .4);
                        color: #F0F2F5;
                        font-weight: bold;
                        border: 2px solid rgb(92, 173, 214);
                    }
                """)

            button.clicked.connect(lambda checked=False, r=reps: self.switch_representation(r))
            layout.addWidget(button)

    def switch_representation(self, representations):
        """Switch to a different representation in RV."""
        if not representations:
            return

        new_rep = representations[0]
        new_path = new_rep.get('path', '')

        if not new_path:
            show_message_dialog("Error", "No valid path.", level="warning", parent=self.parent)
            return

        try:
            import rv.commands as commands
            norm_path = Path(new_path).as_posix()

            if norm_path in self.loaded_representations:
                self._switch_to_loaded(norm_path, new_path, commands)
            else:
                self._load_new_representation(new_path, norm_path, commands)

        except Exception as e:
            show_message_dialog("Error", str(e), level="critical", parent=self.parent)

    def _switch_to_loaded(self, norm_path, new_path, commands):
        source_group = self.loaded_representations[norm_path]
        if source_group and commands.nodeExists(source_group):
            commands.setViewNode(source_group)
            self.parent.current_version_data['current_representation_path'] = new_path
            if hasattr(self.parent, 'rv_integration') and self.parent.rv_integration:
                self.parent.rv_integration._debounced_update()
            self.update_tab(self.parent.current_version_data)
        else:
            del self.loaded_representations[norm_path]
            self.switch_representation([{'path': new_path}])

    def _load_new_representation(self, new_path, norm_path, commands):
        """Load using official loaders."""
        try:
            import ayon_api
            from ayon_openrv.plugins.load.openrv.load_mov import MovLoader
            from ayon_openrv.plugins.load.openrv.load_frames import FramesLoader

            rep_id = next((r['id'] for r in self.parent.current_version_data.get('representations', [])
                           if r.get('path') == new_path), None)
            if not rep_id:
                raise ValueError("Representation ID not found")

            project_name = self.parent.current_version_data['project_name']
            version_id = self.parent.current_version_data['version_id']

            project = ayon_api.get_project(project_name)
            representation = ayon_api.get_representation_by_id(project_name, rep_id)
            version = ayon_api.get_version_by_id(project_name, version_id)
            product = ayon_api.get_product_by_id(project_name, version['productId'])
            folder = ayon_api.get_folder_by_id(project_name, product['folderId'])

            context = {
                'project': project,
                'folder': folder,
                'product': product,
                'version': version,
                'representation': representation
            }

            ext = Path(new_path).suffix.lower()
            loader_class = MovLoader if ext in ['.mov', '.mp4'] else FramesLoader
            loader = loader_class(context)
            loader.load(context, name=product['name'], namespace=folder['name'])

            sources = commands.sourcesAtFrame(commands.frame())
            if sources:
                self.loaded_representations[norm_path] = commands.nodeGroup(sources[0])

            self.parent.current_version_data['current_representation_path'] = new_path
            self.update_tab(self.parent.current_version_data)

        except Exception as e:
            print(f"⚠️ Loader failed: {e}")
            import traceback
            traceback.print_exc()
            show_message_dialog("Error", str(e), level="critical", parent=self.parent)
