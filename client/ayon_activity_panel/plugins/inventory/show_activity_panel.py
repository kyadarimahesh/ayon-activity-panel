"""Scene Inventory action to show Activity Panel."""
import logging
from ayon_core.pipeline import InventoryAction

log = logging.getLogger(__name__)


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
        if not containers:
            log.warning("No containers selected")
            return

        container = containers[0]
        
        try:
            from ayon_activity_panel import ActivityPanel
            from qtpy.QtWidgets import QDockWidget, QApplication
            from qtpy.QtCore import Qt
        except ImportError as e:
            log.error(f"Failed to import Activity Panel: {e}")
            return

        # Get main window
        main_window = None
        for widget in QApplication.topLevelWidgets():
            if widget.objectName() in ["SceneInventory", "MainWindow"]:
                main_window = widget
                break

        if not main_window:
            log.warning("Could not find main window")
            return

        # Create or show existing panel
        existing_dock = main_window.findChild(QDockWidget, "ActivityPanelDock")
        if existing_dock:
            existing_dock.show()
            existing_dock.raise_()
            panel = existing_dock.widget()
        else:
            # Create new panel
            panel = ActivityPanel(bind_rv_events=False)
            dock = QDockWidget("AYON Activity Panel", main_window)
            dock.setObjectName("ActivityPanelDock")
            dock.setWidget(panel)
            main_window.addDockWidget(Qt.RightDockWidgetArea, dock)
            dock.show()

        # Set version data from container
        version_id = container.get("representation")
        if not version_id:
            log.warning("No version ID in container")
            return

        version_data = {
            "version_id": version_id,
            "current_version": container.get("version", "N/A"),
            "path": container.get("namespace", ""),
        }
        
        panel.set_version(version_id, version_data)
        log.info(f"Opened Activity Panel for container: {container.get('name')}")
