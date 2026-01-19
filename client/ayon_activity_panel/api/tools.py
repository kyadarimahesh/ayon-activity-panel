"""Helper tools for showing Activity Panel across different hosts."""

from ayon_activity_panel.api.lib import qt_app_context


class ActivityPanelHelper:
    """Create and cache Activity Panel dock widget in memory."""

    def __init__(self, parent=None):
        self._parent = parent
        self._activity_panel_dock = None

    def get_activity_panel_dock(self, parent, project_name=None, bind_rv_events=False):
        """Create, cache and return Activity Panel dock widget."""
        if self._activity_panel_dock is None:
            from ayon_activity_panel import ActivityPanel
            from ayon_core.pipeline import get_current_project_name
            from qtpy.QtWidgets import QDockWidget
            from qtpy.QtCore import Qt, QSettings
            import ayon_api
            
            if project_name is None:
                project_name = get_current_project_name()
            
            panel = ActivityPanel(
                project_name=project_name,
                parent=parent or self._parent,
                bind_rv_events=bind_rv_events
            )
            
            dock = QDockWidget("Activity Panel", parent or self._parent)
            dock.setWidget(panel)
            
            if parent or self._parent:
                (parent or self._parent).addDockWidget(Qt.RightDockWidgetArea, dock)
            
            settings = QSettings("AYON", "ActivityPanelAddon")
            if splitter_state := settings.value("splitter_state"):
                panel.ui.mainSplitter.restoreState(splitter_state)
            if dock_geometry := settings.value("dock_geometry"):
                dock.restoreGeometry(dock_geometry)
            
            dock.destroyed.connect(
                lambda: settings.setValue("splitter_state", panel.ui.mainSplitter.saveState())
            )
            
            if bind_rv_events:
                panel.enable_rv_events()
            
            self._activity_panel_dock = dock

        return self._activity_panel_dock

    def show_activity_panel(self, parent=None, project_name=None, bind_rv_events=False):
        """Show Activity Panel dock widget."""
        with qt_app_context():
            activity_panel_dock = self.get_activity_panel_dock(parent, project_name, bind_rv_events)
            activity_panel_dock.show()
            activity_panel_dock.raise_()


class _SingletonPoint:
    """Singleton access to Activity Panel."""
    helper = None

    @classmethod
    def _create_helper(cls):
        if cls.helper is None:
            cls.helper = ActivityPanelHelper()

    @classmethod
    def show_activity_panel(cls, parent=None, project_name=None, bind_rv_events=False):
        cls._create_helper()
        cls.helper.show_activity_panel(parent, project_name, bind_rv_events)

    @classmethod
    def get_activity_panel_dock(cls, parent=None, project_name=None, bind_rv_events=False):
        cls._create_helper()
        return cls.helper.get_activity_panel_dock(parent, project_name, bind_rv_events)


# Public API
def show_activity_panel(parent=None, project_name=None, bind_rv_events=False):
    """Show Activity Panel as a docked widget with singleton pattern.
    
    Args:
        parent: Parent widget
        project_name: Project name (auto-detected if None)
        bind_rv_events: Whether to bind RV events (for OpenRV host)
        
    Returns:
        QDockWidget: The dock widget containing the panel
    """
    _SingletonPoint.show_activity_panel(parent, project_name, bind_rv_events)
    return _SingletonPoint.get_activity_panel_dock(parent, project_name, bind_rv_events)
