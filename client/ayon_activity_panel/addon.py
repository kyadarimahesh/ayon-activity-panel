from __future__ import annotations

import os

try:
    from ayon_core.addon import AYONAddon, IPluginPaths

    AYON_CORE_AVAILABLE = True
except ImportError:

    # Dummy base classes for standalone mode
    class AYONAddon:
        pass


    class IPluginPaths:
        pass

from .version import __version__


class ActivityPanelAddon(AYONAddon, IPluginPaths):
    """Activity Panel addon for AYON.
    
    Provides a reusable activity panel widget for displaying version activities,
    comments, and status changes across AYON applications.
    """

    name = "activity_panel"
    version = __version__

    def initialize(self, settings):
        """Initialize addon with settings."""
        # Extract activity_panel settings from studio settings
        addon_settings = settings.get(self.name, {})
        self._settings = {
            'enabled': addon_settings.get('enabled', True),
            'debounce_delay_ms': addon_settings.get('debounce_delay_ms', 500),
            'auto_refresh_interval_ms': addon_settings.get('auto_refresh_interval_ms', 300000),
            'enable_rv_integration': addon_settings.get('enable_rv_integration', True),
        }

    def connect_with_addons(self, enabled_addons):
        """Connect with other addons."""
        pass

    def get_settings(self):
        """Get addon settings.
        
        Returns:
            dict: Addon settings.
        """
        return self._settings

    def get_plugin_paths(self):
        """Return plugin paths for the addon.
        
        Returns:
            dict: Empty dict as this addon provides widgets, not plugins.
        """
        return {}

    def get_loader_action_plugin_paths(self):
        """Return loader action plugin paths for Tray Browser.
        
        Returns:
            list: List of loader action plugin paths.
        """
        plugins_dir = os.path.join(os.path.dirname(__file__), "plugins")
        return [os.path.join(plugins_dir, "load")]

    def get_load_plugin_paths(self, host_name):
        """Return loader plugin paths (deprecated, kept for compatibility).
        
        Args:
            host_name (str): Name of the host application.
            
        Returns:
            list: Empty list.
        """
        return []

    def get_inventory_action_paths(self, host_name):
        """Return inventory action plugin paths.
        
        Args:
            host_name (str): Name of the host application.
            
        Returns:
            list: List of inventory action plugin paths.
        """
        plugins_dir = os.path.join(os.path.dirname(__file__), "plugins")
        return [os.path.join(plugins_dir, "inventory")]
