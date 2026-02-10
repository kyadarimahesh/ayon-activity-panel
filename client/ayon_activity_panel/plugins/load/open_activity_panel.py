"""Loader action to open Activity Panel in Tray Browser."""
from typing import Optional, Any

from ayon_core.lib import Logger
from ayon_core.pipeline.actions import (
    LoaderSimpleActionPlugin,
    LoaderActionSelection,
    LoaderActionResult,
)

log = Logger.get_logger(__name__)

# Global reference to keep panel alive
_activity_panel_instance = None


class OpenActivityPanelAction(LoaderSimpleActionPlugin):
    """Open Activity Panel for selected version in Tray Browser."""

    label = "Open Activity Panel"
    order = 1
    icon = {
        "type": "awesome-font",
        "name": "fa.comment",
        "color": "#4CAF50",
    }

    def is_compatible(self, selection: LoaderActionSelection) -> bool:
        """Always compatible when versions are selected."""
        return selection.versions_selected()

    def execute_simple_action(
            self,
            selection: LoaderActionSelection,
            form_values: dict[str, Any],
    ) -> Optional[LoaderActionResult]:
        """Show activity panel for the selected version."""
        global _activity_panel_instance

        try:
            from ayon_activity_panel import ActivityPanel
            import ayon_api
        except ImportError as e:
            return LoaderActionResult(
                f"Activity Panel addon not available: {e}",
                success=False,
            )

        versions = selection.get_selected_version_entities()
        if not versions:
            return LoaderActionResult(
                "No version selected",
                success=False,
            )

        version = versions[0]
        version_id = version.get("id")
        project_name = selection.project_name

        log.info(f"Version ID: {version_id}, Project: {project_name}")

        # Reuse existing panel if available
        if _activity_panel_instance is not None:
            try:
                _activity_panel_instance.show()
                _activity_panel_instance.raise_()
                _activity_panel_instance.activateWindow()
                panel = _activity_panel_instance
            except RuntimeError:
                _activity_panel_instance = None

        # Create new panel if needed
        if _activity_panel_instance is None:
            settings = {}
            try:
                from ayon_core.addon import AddonsManager

                manager = AddonsManager()
                addon = manager.get("activity_panel")
                if addon and hasattr(addon, 'get_settings'):
                    settings = addon.get_settings()

                if not settings:
                    settings = ayon_api.get_addon_project_settings(
                        "activity_panel", project_name
                    )
            except Exception:
                pass

            panel = ActivityPanel(project_name=project_name, bind_rv_events=False, settings=settings)
            panel.setWindowTitle("AYON Activity Panel")
            panel.resize(600, 800)
            _activity_panel_instance = panel

        # Set version - panel will auto-build version_data
        panel.set_version(version_id, project_name=project_name)
        panel.show()

        return LoaderActionResult(
            f"Activity Panel opened for version {version_id}",
            success=True,
        )
