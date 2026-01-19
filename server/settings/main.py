from ayon_server.settings import BaseSettingsModel, SettingsField


class DisplaySettings(BaseSettingsModel):
    max_activities_display: int = SettingsField(
        100,
        title="Max Activities to Display",
        ge=10,
        le=500
    )
    enable_progressive_loading: bool = SettingsField(
        True,
        title="Enable Progressive Image Loading"
    )
    parallel_image_workers: int = SettingsField(
        4,
        title="Parallel Image Download Workers",
        ge=1,
        le=10
    )


class CommentSettings(BaseSettingsModel):
    require_comment_text: bool = SettingsField(
        True,
        title="Require Comment Text"
    )
    max_comment_length: int = SettingsField(
        5000,
        title="Max Comment Length",
        ge=100,
        le=10000
    )
    enable_file_attachments: bool = SettingsField(
        True,
        title="Enable File Attachments"
    )
    max_attachment_size_mb: int = SettingsField(
        100,
        title="Max Attachment Size (MB)",
        ge=1,
        le=500
    )


class PerformanceSettings(BaseSettingsModel):
    debounce_delay_ms: int = SettingsField(
        300,
        title="Debounce Delay (milliseconds)",
        ge=100,
        le=1000
    )
    cache_activities: bool = SettingsField(
        True,
        title="Cache Activities Locally"
    )
    cache_duration_minutes: int = SettingsField(
        5,
        title="Cache Duration (minutes)",
        ge=1,
        le=60
    )


class ActivityPanelSettings(BaseSettingsModel):
    enabled: bool = SettingsField(
        True,
        title="Enable Activity Panel"
    )
    display: DisplaySettings = SettingsField(
        default_factory=DisplaySettings,
        title="Display Settings"
    )
    comments: CommentSettings = SettingsField(
        default_factory=CommentSettings,
        title="Comment Settings"
    )
    performance: PerformanceSettings = SettingsField(
        default_factory=PerformanceSettings,
        title="Performance Settings"
    )


DEFAULT_VALUES = {
    "enabled": True,
    "display": {
        "max_activities_display": 100,
        "enable_progressive_loading": True,
        "parallel_image_workers": 4
    },
    "comments": {
        "require_comment_text": True,
        "max_comment_length": 5000,
        "enable_file_attachments": True,
        "max_attachment_size_mb": 100
    },
    "performance": {
        "debounce_delay_ms": 300,
        "cache_activities": True,
        "cache_duration_minutes": 5
    }
}
