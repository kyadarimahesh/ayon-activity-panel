"""Abstract interfaces for Activity Panel.

Following AYON core architecture pattern:
- BackendActivityPanelController: Backend logic interface
- FrontendActivityPanelController: Frontend/UI interaction interface

The controller (control.py) should implement BOTH interfaces.
The widget should only interact through these interfaces.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional, Any


class _BaseActivityPanelController(ABC):
    """Base controller interface with shared methods."""

    @abstractmethod
    def get_project_name(self) -> Optional[str]:
        """Get current project name.

        Returns:
            Current project name or None.
        """
        pass

    @abstractmethod
    def get_current_version_id(self) -> Optional[str]:
        """Get current version ID.

        Returns:
            Current version ID or None.
        """
        pass

    @abstractmethod
    def get_current_version_data(self) -> Optional[dict[str, Any]]:
        """Get current version data.

        Returns:
            Current version data dictionary or None.
        """
        pass

    @abstractmethod
    def get_available_statuses(self) -> list[dict[str, Any]]:
        """Get available statuses for current context.

        Returns:
            List of status dictionaries.
        """
        pass


class BackendActivityPanelController(_BaseActivityPanelController):
    """Backend controller interface - handles data operations."""

    @abstractmethod
    def set_project(self, project_name: str) -> bool:
        """Set current project and fetch statuses.

        Args:
            project_name: Project name to set.

        Returns:
            True if successful.
        """
        pass

    @abstractmethod
    def build_version_data(
            self,
            version_id: str,
            project_name: Optional[str] = None
    ) -> Optional[dict[str, Any]]:
        """Build version data from version ID.

        Args:
            version_id: Version ID to build data for.
            project_name: Optional project name override.

        Returns:
            Version data dictionary or None if failed.
        """
        pass

    @abstractmethod
    def update_version_status(
            self,
            version_id: str,
            new_status: str,
            is_task: bool = False
    ) -> bool:
        """Update version or task status.

        Args:
            version_id: Version or task ID.
            new_status: New status value.
            is_task: Whether updating task status.

        Returns:
            True if successful.
        """
        pass

    @abstractmethod
    def fetch_statuses(self, is_task: bool = False) -> list[dict[str, Any]]:
        """Fetch available statuses.

        Args:
            is_task: Whether to fetch task statuses.

        Returns:
            List of status dictionaries.
        """
        pass

    @abstractmethod
    def fetch_activities(
            self,
            version_id: str,
            version_data: dict[str, Any],
            activity_types: Optional[list[str]] = None
    ) -> list[dict[str, Any]]:
        """Fetch activities for a version.

        Args:
            version_id: Version ID.
            version_data: Version data dictionary.
            activity_types: Optional filter for activity types.

        Returns:
            List of activity dictionaries.
        """
        pass

    @abstractmethod
    def build_version_data_from_node(
            self,
            version_node: dict[str, Any],
            current_version_data: Optional[dict[str, Any]] = None
    ) -> dict[str, Any]:
        """Build version data from a version node.

        Args:
            version_node: Raw version node from API.
            current_version_data: Current version data for context.

        Returns:
            Version data dictionary.
        """
        pass


class FrontendActivityPanelController(_BaseActivityPanelController):
    """Frontend controller interface - handles UI interactions."""

    @abstractmethod
    def register_event_callback(self, topic: str, callback) -> None:
        """Register callback for an event topic.

        Args:
            topic: Event topic name.
            callback: Callback function.
        """
        pass

    @abstractmethod
    def emit_event(
            self,
            topic: str,
            data: Optional[dict[str, Any]] = None,
            source: Optional[str] = None
    ) -> None:
        """Emit an event.

        Args:
            topic: Event topic name.
            data: Optional event data.
            source: Optional event source identifier.
        """
        pass

    @abstractmethod
    def set_version(
            self,
            version_id: str,
            version_data: Optional[dict[str, Any]] = None,
            project_name: Optional[str] = None

    ) -> None:
        """Set current version and notify listeners.

        Args:
            version_id: Version ID to set.
            version_data: Optional pre-built version data.
            project_name: Optional project name override.
        """
        pass

    @abstractmethod
    def refresh(self) -> None:
        """Refresh current version data and activities."""
        pass

    @abstractmethod
    def clear(self) -> None:
        """Clear all data and reset state."""
        pass
