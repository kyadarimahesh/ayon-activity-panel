"""Version comparison manager for RV."""
import logging
from pathlib import Path
import os
import re

log = logging.getLogger(__name__)


class ComparisonManager:
    """Manages version comparison in RV."""

    def __init__(self, parent):
        """Initialize comparison manager.
        
        Args:
            parent: Parent widget.
        """
        self.parent = parent
        self.comparison_stack_node = None
        self.comparison_layout_node = None
        self.comparison_sources = {}

    def create_comparison_stack(self, old_version_data, new_version_data, set_view_to_new=True, existing_source=None):
        """Create comparison stack and layout in RV.
        
        Args:
            old_version_data (dict): Old version data.
            new_version_data (dict): New version data.
            set_view_to_new (bool): Set view to new version.
            existing_source (str): Existing source node.
        """

        try:
            import rv.commands as commands

            new_version_id = new_version_data.get('version_id')
            old_version_id = old_version_data.get('version_id')

            if self.comparison_stack_node and commands.nodeExists(self.comparison_stack_node):
                if new_version_id in self.comparison_sources:
                    target_source = self.comparison_sources[new_version_id]
                    if commands.nodeExists(target_source):
                        commands.setViewNode(target_source)
                        return

            current_view = existing_source or commands.viewNode()
            old_source_group = None
            if current_view:
                node_type = commands.nodeType(current_view)

                # Check if current view is the old version (standalone source)
                if node_type == "RVSourceGroup":
                    source_nodes = commands.nodesInGroup(current_view)
                    for node in source_nodes:
                        if commands.propertyExists(f"{node}.ayon.version_id"):
                            vid = commands.getStringProperty(f"{node}.ayon.version_id")[0]
                            if vid == old_version_id:
                                old_source_group = current_view
                                break
                        else:
                            log.debug(f"No ayon.version_id on node {node}")

                # Check if old version is in sequence
                elif node_type == "RVSequenceGroup":
                    inputs = commands.nodeConnections(current_view, False)[0]
                    for source in inputs:
                        source_nodes = commands.nodesInGroup(source)
                        for node in source_nodes:
                            if commands.propertyExists(f"{node}.ayon.version_id"):
                                vid = commands.getStringProperty(f"{node}.ayon.version_id")[0]
                                if vid == old_version_id:
                                    old_source_group = source
                                    break
                        if old_source_group:
                            break

            old_rep_path = old_version_data.get('current_representation_path', '')
            old_ext = Path(old_rep_path).suffix.lower() if old_rep_path else None

            new_representations = new_version_data.get('representations', [])
            new_rep_path = None

            if old_ext:
                for rep in new_representations:
                    rep_path = rep.get('path', '')
                    if rep_path and Path(rep_path).suffix.lower() == old_ext:
                        new_rep_path = rep_path
                        break

            if not new_rep_path and new_representations:
                new_rep_path = new_representations[0].get('path', '')

            if not new_rep_path:
                log.warning("No representations available for new version")
                return

            old_load_path = self._prepare_load_path(old_rep_path)
            new_load_path = self._prepare_load_path(new_rep_path)

            if not old_source_group:
                old_nodes = commands.addSourcesVerbose([[old_load_path]])
                if not old_nodes:
                    log.error("Failed to load old version")
                    return
                old_source_group = commands.nodeGroup(old_nodes[0])
                self._store_comparison_metadata(old_nodes[0], old_version_data)

            new_nodes = commands.addSourcesVerbose([[new_load_path]])
            if not new_nodes:
                log.error("Failed to load new version")
                return

            new_source_group = commands.nodeGroup(new_nodes[0])

            self._store_comparison_metadata(new_nodes[0], new_version_data)

            self.comparison_sources[old_version_id] = old_source_group
            self.comparison_sources[new_version_id] = new_source_group

            product_name = old_version_data.get('product_name') or new_version_data.get('product_name') or 'Unknown'
            old_version = old_version_data.get('current_version', 'v001')
            new_version = new_version_data.get('current_version', 'v002')
            comparison_name = f"{product_name}_{old_version}_vs_{new_version}"

            stack_node = commands.newNode("RVStackGroup")
            commands.setNodeInputs(stack_node, [old_source_group, new_source_group])
            commands.setStringProperty(f"{stack_node}.ui.name", [comparison_name])
            self.comparison_stack_node = stack_node

            layout_node = commands.newNode("RVLayoutGroup")
            commands.setNodeInputs(layout_node, [old_source_group, new_source_group])
            commands.setStringProperty(f"{layout_node}.layout.mode", ["packed"])
            commands.setStringProperty(f"{layout_node}.ui.name", [comparison_name])
            self.comparison_layout_node = layout_node

            if set_view_to_new:
                commands.setViewNode(new_source_group)
            else:
                commands.setViewNode(stack_node)

            commands.setFrame(1)

        except Exception as e:
            log.error(f"Failed to create comparison: {str(e)}")
            import traceback
            traceback.print_exc()

    def _prepare_load_path(self, path):
        """Prepare path for RV loading (handle sequences)."""
        ext = Path(path).suffix.lower()

        if ext in ['.exr', '.jpg', '.jpeg', '.png', '.tiff', '.dpx']:
            folder = os.path.dirname(path)
            filename = os.path.basename(path)

            match = re.match(r"^(.*?)(\d+)(\.[^.]+)$", filename)
            if match and os.path.exists(folder):
                prefix, frame_str, ext = match.groups()
                frames = []

                for f in os.listdir(folder):
                    m = re.match(rf"^{re.escape(prefix)}(\d+){re.escape(ext)}$", f)
                    if m:
                        frames.append(int(m.group(1)))

                if frames:
                    start, end = min(frames), max(frames)
                    return os.path.join(folder, f"{prefix}{start}-{end}#{ext}")

        return path

    @staticmethod
    def _store_comparison_metadata(node, version_data):
        """Store version metadata on comparison source nodes."""
        try:
            import rv.commands as commands
            import json

            # Get actual file path from RV
            file_path = None
            try:
                media = commands.sourceMedia(node)
                if media:
                    file_path = media[0] if isinstance(media, (list, tuple)) else media
                    log.debug(f"Read file_path from RV: {file_path}")
            except Exception as e:
                log.warning(f"Could not read sourceMedia: {e}")

            metadata = {
                'version_id': version_data.get('version_id'),
                'version_name': version_data.get('current_version'),
                'version_status': version_data.get('version_status'),
                'author': version_data.get('author'),
                'product_name': version_data.get('product_name'),
                'folder_path': version_data.get('path'),
                'file_path': file_path or version_data.get('current_representation_path'),
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
            import traceback
            traceback.print_exc()
