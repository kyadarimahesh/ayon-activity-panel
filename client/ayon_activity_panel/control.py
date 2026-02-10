"""Activity Panel Controller.

Following AYON core architecture pattern:
- Implements both BackendActivityPanelController and FrontendActivityPanelController
- Manages state and coordinates between services and UI
- Uses event system for frontend communication
"""
from __future__ import annotations

from typing import Optional, Any, Callable

from ayon_core.lib import Logger
from ayon_core.lib.events import QueuedEventSystem

from .abstract import (
    BackendActivityPanelController,
    FrontendActivityPanelController,
)
from .api.ayon.activity_service import ActivityService
from .api.ayon.version_service import VersionService

log = Logger.get_logger(__name__)


class ActivityPanelController(
    BackendActivityPanelController,
    FrontendActivityPanelController
):
    """Controller for Activity Panel.

    Implements both backend and frontend interfaces following AYON patterns.
    Coordinates between services and provides event-based communication.
    """

    def __init__(self):
        """Initialize controller with services and event system."""
        self._project_name: Optional[str] = None
        self._current_version_id: Optional[str] = None
        self._current_version_data: Optional[dict[str, Any]] = None
        self._available_statuses: list[dict[str, Any]] = []

        # Services
        self._activity_service = ActivityService()
        self._version_service = VersionService()

        # Event system for frontend communication
        self._event_system = QueuedEventSystem()

    # -------------------------------------------------------------------------
    # Properties for service access (if needed by managers)
    # -------------------------------------------------------------------------
    @property
    def activity_service(self) -> ActivityService:
        """Access to activity service."""
        return self._activity_service

    @property
    def version_service(self) -> VersionService:
        """Access to version service."""
        return self._version_service

    # -------------------------------------------------------------------------
    # _BaseActivityPanelController implementation
    # -------------------------------------------------------------------------
    def get_project_name(self) -> Optional[str]:
        """Get current project name."""
        return self._project_name

    def get_current_version_id(self) -> Optional[str]:
        """Get current version ID."""
        return self._current_version_id

    def get_current_version_data(self) -> Optional[dict[str, Any]]:
        """Get current version data."""
        return self._current_version_data

    def get_available_statuses(self) -> list[dict[str, Any]]:
        """Get available statuses for current context."""
        return self._available_statuses

    # -------------------------------------------------------------------------
    # BackendActivityPanelController implementation
    # -------------------------------------------------------------------------
    def set_project(self, project_name: str) -> bool:
        """Set current project and fetch statuses."""
        try:
            self._project_name = project_name

            if project_name:
                statuses = self._version_service.get_version_statuses(project_name)
                if statuses:
                    self._available_statuses = statuses
                    self.emit_event("project.changed", {"project_name": project_name})
                    return True
            return False
        except Exception:
            log.error(f"Failed to set project: {project_name}", exc_info=True)
            return False

    def build_version_data(
            self,
            version_id: str,
            project_name: Optional[str] = None
    ) -> Optional[dict[str, Any]]:
        """Build version data from version ID."""
        proj = project_name or self._project_name
        if not proj:
            log.error("No project_name provided and no project set")
            return None

        try:
            version_data = self._version_service.build_version_data_from_id(
                proj, version_id
            )
            if not version_data:
                log.error(f"Failed to build version_data for {version_id}")
                return None
            return version_data
        except Exception:
            log.error(f"Exception building version data for {version_id}", exc_info=True)
            return None

    def update_version_status(
            self,
            version_id: str,
            new_status: str,
            is_task: bool = False
    ) -> bool:
        """Update version or task status."""
        if not self._project_name:
            log.error("No project set")
            return False

        try:
            if is_task:
                success = self._version_service.update_task_status(
                    self._project_name, version_id, new_status
                )
            else:
                success = self._version_service.update_version_status(
                    self._project_name, version_id, new_status
                )

            if success:
                self.emit_event("status.changed", {
                    "version_id": version_id,
                    "new_status": new_status,
                    "is_task": is_task
                })
            return success
        except Exception:
            log.error(f"Failed to update status to {new_status}", exc_info=True)
            return False

    def fetch_statuses(self, is_task: bool = False) -> list[dict[str, Any]]:
        """Fetch available statuses."""
        if not self._project_name:
            return []

        try:
            if is_task:
                statuses = self._version_service.get_task_statuses(self._project_name)
            else:
                statuses = self._version_service.get_version_statuses(self._project_name)
            self._available_statuses = statuses
            return statuses
        except Exception:
            log.error("Failed to fetch statuses", exc_info=True)
            return []

    def fetch_activities(
            self,
            version_id: str,
            version_data: dict[str, Any],
            activity_types: Optional[list[str]] = None
    ) -> list[dict[str, Any]]:
        """Fetch activities for a version."""
        if not self._project_name:
            return []

        try:
            dcc_mode = 'version_id' not in version_data
            task_id = version_data.get('task_id')

            entity_ids = [task_id] if dcc_mode and task_id else [version_id]
            if not dcc_mode and task_id and task_id != "N/A":
                entity_ids.append(task_id)

            if activity_types is None:
                activity_types = ['comment', 'status.change', 'version.publish']

            # Use activity service to fetch
            from .api.ayon.ayon_client_api import AyonClient
            client = AyonClient()
            response = client.get_activities(
                project_name=self._project_name,
                entity_ids=entity_ids,
                activity_types=activity_types,
                dcc_mode=dcc_mode,
                last=50
            )

            if response and 'project' in response and response['project']:
                edges = response['project'].get('activities', {}).get('edges', [])
                return [edge['node'] for edge in edges if edge.get('node')]
            return []
        except Exception:
            log.error("Failed to fetch activities", exc_info=True)
            return []

    def build_version_data_from_node(
            self,
            version_node: dict[str, Any],
            current_version_data: Optional[dict[str, Any]] = None
    ) -> dict[str, Any]:
        """Build version data from a version node."""
        import ayon_api

        version_id = version_node.get('id', '')
        current_data = current_version_data or self._current_version_data or {}

        # Fetch representations
        representations = []
        try:
            for rep in ayon_api.get_representations(
                    self._project_name, version_ids=[version_id]
            ):
                representations.append({
                    'id': rep['id'],
                    'name': rep['name'],
                    'path': rep.get('attrib', {}).get('path', '')
                })
        except Exception as e:
            log.error(f"Failed to fetch representations: {e}")

        return {
            'version_id': version_id,
            'project_name': self._project_name,
            'task_id': version_node.get('taskId', ''),
            'product_name': current_data.get('product_name', 'Unknown'),
            'path': current_data.get('path', 'N/A'),
            'current_version': f"v{version_node.get('version', 1):03d}",
            'versions': current_data.get('versions', []),
            'version_status': version_node.get('status', 'N/A'),
            'author': version_node.get('author', 'N/A'),
            'representations': representations,
            'current_representation_path': (
                representations[0].get('path', '') if representations else ''
            )
        }

    # -------------------------------------------------------------------------
    # FrontendActivityPanelController implementation
    # -------------------------------------------------------------------------
    def register_event_callback(self, topic: str, callback: Callable) -> None:
        """Register callback for an event topic."""
        self._event_system.add_callback(topic, callback)

    def emit_event(
            self,
            topic: str,
            data: Optional[dict[str, Any]] = None,
            source: Optional[str] = None
    ) -> None:
        """Emit an event."""
        if data is None:
            data = {}
        self._event_system.emit(topic, data, source)

    def set_version(
            self,
            version_id: str,
            version_data: Optional[dict[str, Any]] = None,
            project_name: Optional[str] = None
    ) -> None:
        """Set current version and notify listeners."""
        # Auto-build version_data if not provided
        if version_data is None:
            version_data = self.build_version_data(version_id, project_name)
            if not version_data:
                log.error(f"Failed to build version_data for {version_id}")
                self.clear()
                return

        # Update project if provided in version_data
        data_project = version_data.get('project_name')
        if data_project and data_project != self._project_name:
            self.set_project(data_project)

        # Check if DCC mode and fetch appropriate statuses
        dcc_mode = 'version_id' not in version_data
        self._available_statuses = self.fetch_statuses(is_task=dcc_mode)

        # Update state
        self._current_version_id = version_id
        self._current_version_data = version_data

        # Emit event for UI to react
        self.emit_event("version.changed", {
            "version_id": version_id,
            "version_data": version_data,
            "dcc_mode": dcc_mode
        })

    def refresh(self) -> None:
        """Refresh current version data and activities."""
        if not self._current_version_id or not self._project_name:
            return

        # Check if DCC mode (task-based) from current version data
        dcc_mode = (
                self._current_version_data and
                'version_id' not in self._current_version_data
        )

        if dcc_mode:
            # In DCC mode, refresh task status only - don't rebuild version data
            task_id = self._current_version_data.get('task_id')
            if task_id:
                try:
                    import ayon_api
                    task = ayon_api.get_task_by_id(self._project_name, task_id)
                    if task:
                        self._current_version_data['version_status'] = task.get('status', 'N/A')
                except Exception:
                    log.error("Failed to refresh task status", exc_info=True)
        else:
            # Version mode - rebuild version data
            fresh_data = self.build_version_data(
                self._current_version_id,
                self._project_name
            )
            if fresh_data:
                self._current_version_data = fresh_data

        self.emit_event("version.refreshed", {
            "version_id": self._current_version_id,
            "version_data": self._current_version_data
        })

    def clear(self) -> None:
        """Clear all data and reset state."""
        self._current_version_id = None
        self._current_version_data = None
        self.emit_event("version.cleared")
