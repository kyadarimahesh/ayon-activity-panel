"""Version comparison manager for RV."""
from pathlib import Path

from ayon_core.lib import Logger

log = Logger.get_logger(__name__)


class ComparisonManager:
    """Manages version comparison in RV."""

    def __init__(self, parent):
        self.parent = parent
        self.comparison_sources = {}

    def create_comparison_stack(self, old_version_data, new_version_data, set_view_to_new=True, existing_source=None):
        """Create comparison stack in RV using official loaders."""
        try:
            import rv.commands as commands
            import ayon_api
            from ayon_openrv.plugins.load.openrv.load_mov import MovLoader
            from ayon_openrv.plugins.load.openrv.load_frames import FramesLoader

            new_version_id = new_version_data.get('version_id')
            old_version_id = old_version_data.get('version_id')
            project_name = new_version_data.get('project_name')

            # Check if already loaded
            if new_version_id in self.comparison_sources:
                target_source = self.comparison_sources[new_version_id]
                if commands.nodeExists(target_source):
                    commands.setViewNode(target_source)
                    return

            # Find old source if exists
            old_source_group = existing_source or self._find_version_source(old_version_id)

            # Get matching representation for new version
            new_rep = self._get_matching_representation(old_version_data, new_version_data)
            if not new_rep:
                log.warning("No matching representation for comparison")
                return

            # Load new version using official loader
            new_source_group = self._load_version_with_loader(
                project_name, new_version_id, new_rep, MovLoader, FramesLoader
            )
            if not new_source_group:
                return

            # Load old version if not found
            if not old_source_group:
                old_rep = self._get_representation(old_version_data)
                if old_rep:
                    old_source_group = self._load_version_with_loader(
                        project_name, old_version_id, old_rep, MovLoader, FramesLoader
                    )

            if old_source_group and new_source_group:
                self._create_rv_comparison(old_source_group, new_source_group, old_version_data, new_version_data)

            self.comparison_sources[new_version_id] = new_source_group
            if old_source_group:
                self.comparison_sources[old_version_id] = old_source_group

            if set_view_to_new:
                commands.setViewNode(new_source_group)

        except Exception as e:
            log.error(f"Comparison failed: {e}")
            import traceback
            traceback.print_exc()

    def _find_version_source(self, version_id):
        """Find existing source for version."""
        try:
            import rv.commands as commands
            for node in commands.nodesOfType("RVFileSource"):
                if commands.propertyExists(f"{node}.ayon.version_id"):
                    vid = commands.getStringProperty(f"{node}.ayon.version_id")[0]
                    if vid == version_id:
                        return commands.nodeGroup(node)
        except:
            pass
        return None

    def _get_matching_representation(self, old_version_data, new_version_data):
        """Get representation matching old version's extension."""
        old_path = old_version_data.get('current_representation_path', '')
        old_ext = Path(old_path).suffix.lower() if old_path else None

        new_reps = new_version_data.get('representations', [])
        if not new_reps:
            return None

        # Match by extension
        if old_ext:
            for rep in new_reps:
                if Path(rep.get('path', '')).suffix.lower() == old_ext:
                    return rep

        # Fallback to first
        return new_reps[0]

    def _get_representation(self, version_data):
        """Get first available representation."""
        reps = version_data.get('representations', [])
        return reps[0] if reps else None

    def _load_version_with_loader(self, project_name, version_id, rep, MovLoader, FramesLoader):
        """Load version using official loader."""
        try:
            import ayon_api
            import rv.commands as commands

            rep_id = rep.get('id')
            if not rep_id:
                return None

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

            ext = Path(rep.get('path', '')).suffix.lower()
            loader_class = MovLoader if ext in ['.mov', '.mp4'] else FramesLoader
            loader = loader_class(context)
            loader.load(context, name=product['name'], namespace=folder['name'])

            sources = commands.sourcesAtFrame(commands.frame())
            return commands.nodeGroup(sources[0]) if sources else None

        except Exception as e:
            log.error(f"Loader failed: {e}")
            return None

    def _create_rv_comparison(self, old_source, new_source, old_data, new_data):
        """Create RV stack and layout groups."""
        try:
            import rv.commands as commands

            product = old_data.get('product_name', 'Unknown')
            old_ver = old_data.get('current_version', 'v001')
            new_ver = new_data.get('current_version', 'v002')
            name = f"{product}_{old_ver}_vs_{new_ver}"

            # Stack group
            stack = commands.newNode("RVStackGroup")
            commands.setNodeInputs(stack, [old_source, new_source])
            commands.setStringProperty(f"{stack}.ui.name", [name])

            # Layout group
            layout = commands.newNode("RVLayoutGroup")
            commands.setNodeInputs(layout, [old_source, new_source])
            commands.setStringProperty(f"{layout}.layout.mode", ["packed"])
            commands.setStringProperty(f"{layout}.ui.name", [name])

        except Exception as e:
            log.error(f"Failed to create RV groups: {e}")
