"""Loader action to open Activity Panel."""
import logging
from ayon_core.pipeline import load

log = logging.getLogger(__name__)


class OpenActivityPanel(load.LoaderPlugin):
    """Open Activity Panel for selected version."""

    families = ["*"]
    representations = ["*"]
    label = "Open Activity Panel"
    order = 100
    icon = "comment"

    def load(self, context, name=None, namespace=None, options=None):
        """Show activity panel for the selected version.
        
        Args:
            context (dict): Loader context with version information.
            name (str): Not used.
            namespace (str): Not used.
            options (dict): Not used.
        """
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
            if widget.objectName() == "MainWindow":
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
            return

        # Create new panel
        panel = ActivityPanel(bind_rv_events=False)
        dock = QDockWidget("AYON Activity Panel", main_window)
        dock.setObjectName("ActivityPanelDock")
        dock.setWidget(panel)
        main_window.addDockWidget(Qt.RightDockWidgetArea, dock)
        dock.show()

        # Set version data
        version_id = context["version"]["id"]
        project_name = context["project"]["name"]
        
        version_data = {
            "version_id": version_id,
            "project_name": project_name,
            "current_version": context["version"]["name"],
            "path": context.get("folder", {}).get("path", ""),
        }
        
        panel.set_project(project_name)
        panel.set_version(version_id, version_data)
        
        log.info(f"Opened Activity Panel for version: {version_id}")
