from ayon_server.settings import BaseSettingsModel, SettingsField


class ActivityPanelSettings(BaseSettingsModel):
    """Activity Panel addon settings."""

    enabled: bool = SettingsField(
        True,
        title="Enable Activity Panel",
        description="Enable activity panel across all hosts"
    )

    debounce_delay_ms: int = SettingsField(
        500,
        title="RV Navigation Debounce (ms)",
        description="Delay before updating panel during RV navigation",
        ge=100,
        le=2000
    )

    auto_refresh_interval_ms: int = SettingsField(
        300000,
        title="Auto Refresh Interval (ms)",
        description="Interval for auto-refreshing activities (5 minutes default)",
        ge=60000,
        le=600000
    )

    enable_rv_integration: bool = SettingsField(
        True,
        title="Enable RV Integration",
        description="Bind to RV events for automatic updates"
    )


DEFAULT_VALUES = {
    "enabled": True,
    "debounce_delay_ms": 500,
    "auto_refresh_interval_ms": 300000,
    "enable_rv_integration": True
}

