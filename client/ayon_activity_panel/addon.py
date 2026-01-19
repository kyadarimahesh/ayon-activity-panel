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
from .constants import ACTIVITY_PANEL_ROOT_DIR


class ActivityPanelAddon(AYONAddon, IPluginPaths):
    """Activity Panel addon for AYON.
    
    Provides a reusable activity panel widget for displaying version activities,
    comments, and status changes across AYON applications.
    """

    name = "activity_panel"
    version = __version__

    def initialize(self, settings):
        """Initialize addon with settings."""
        pass

    def connect_with_addons(self, enabled_addons):
        """Connect with other addons."""
        pass

    def get_plugin_paths(self):
        """Return plugin paths for the addon.
        
        Returns:
            dict: Empty dict as this addon provides widgets, not plugins.
        """
        return {}

    def get_load_plugin_paths(self, host_name):
        """Return loader plugin paths.
        
        Note: This only works for hosts where Activity Panel is explicitly
        integrated (OpenRV, Review Browser). For other hosts (Nuke, Maya),
        users should access Activity Panel through Scene Inventory actions.
        
        Args:
            host_name (str): Name of the host application.
            
        Returns:
            list: List of loader plugin paths.
        """
        # Only provide loader plugins for specific hosts
        if host_name in ["openrv", "traypublisher"]:
            plugins_dir = os.path.join(ACTIVITY_PANEL_ROOT_DIR, "plugins")
            return [os.path.join(plugins_dir, "load")]
        return []

    def get_inventory_action_paths(self, host_name):
        """Return inventory action plugin paths.
        
        Args:
            host_name (str): Name of the host application.
            
        Returns:
            list: List of inventory action plugin paths.
        """
        plugins_dir = os.path.join(ACTIVITY_PANEL_ROOT_DIR, "plugins")
        return [os.path.join(plugins_dir, "inventory")]
