from typing import Type
from ayon_server.addons import BaseServerAddon
from .settings.main import ActivityPanelSettings, DEFAULT_VALUES


class ActivityPanelAddon(BaseServerAddon):
    """Server-side Activity Panel addon.
    
    Provides settings management for the Activity Panel addon.
    """
    
    settings_model: Type[ActivityPanelSettings] = ActivityPanelSettings

    async def get_default_settings(self):
        """Get default settings for the addon.
        
        Returns:
            ActivityPanelSettings: Default settings instance.
        """
        settings_model_cls = self.get_settings_model()
        return settings_model_cls(**DEFAULT_VALUES)
