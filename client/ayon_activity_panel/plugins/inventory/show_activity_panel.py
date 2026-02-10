"""Scene Inventory action to show Activity Panel."""
from ayon_core.lib import Logger
from ayon_core.pipeline import InventoryAction, get_current_project_name

log = Logger.get_logger(__name__)

# Global reference to prevent garbage collection
_activity_panel_window = None


class ShowActivityPanel(InventoryAction):
    """Show Activity Panel for selected container."""

    label = "Show Activity Panel"
    icon = "comment"
    order = 50

    def process(self, containers):
        """Show activity panel for the first selected container.

        Args:
            containers (list): List of selected containers.
        """
        global _activity_panel_window

        if not containers:
            log.warning("No containers selected")
            return

        container = containers[0]

        try:
            from ayon_activity_panel import ActivityPanel
            from qtpy.QtWidgets import QWidget, QVBoxLayout
        except ImportError as e:
            log.error(f"Failed to import Activity Panel: {e}")
            return

        # Create or reuse floating window
        if _activity_panel_window is None or not _activity_panel_window.isVisible():
            settings = {}
            try:
                from ayon_core.addon import AddonsManager
                import ayon_api

                manager = AddonsManager()
                addon = manager.get("activity_panel")
                if addon and hasattr(addon, 'get_settings'):
                    settings = addon.get_settings()

                if not settings:
                    project_name = get_current_project_name()
                    settings = ayon_api.get_addon_project_settings(
                        "activity_panel", project_name
                    )
            except Exception:
                pass

            window = QWidget()
            window.setWindowTitle("AYON Activity Panel")
            window.resize(800, 600)
            layout = QVBoxLayout(window)
            layout.setContentsMargins(0, 0, 0, 0)
            panel = ActivityPanel(bind_rv_events=False, settings=settings)
            layout.addWidget(panel)
            _activity_panel_window = window
        else:
            window = _activity_panel_window
            panel = window.findChild(ActivityPanel)

        window.show()
        window.raise_()
        window.activateWindow()

        # Fetch version data from container
        representation_id = container.get("representation")
        if not representation_id:
            log.warning("No representation ID in container")
            return

        from ayon_api import get_representation_by_id

        project_name = get_current_project_name()
        representation = get_representation_by_id(project_name, representation_id)
        if not representation:
            log.warning(f"Representation not found: {representation_id}")
            return

        version_id = representation["versionId"]

        # Set version - panel will auto-build version_data
        panel.set_version(version_id, project_name=project_name)
        log.info(f"Opened Activity Panel for container: {container.get('name')}")
        return True
