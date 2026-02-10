"""Standalone AYON Activity Panel - Reusable across all DCC applications."""

from .version import __version__
from .widget import ActivityPanel
from .control import ActivityPanelController
from .abstract import (
    BackendActivityPanelController,
    FrontendActivityPanelController,
)
from .api.tools import show_activity_panel

try:
    from .addon import ActivityPanelAddon

    __all__ = (
        "__version__",
        "ActivityPanelAddon",
        "ActivityPanel",
        "ActivityPanelController",
        "BackendActivityPanelController",
        "FrontendActivityPanelController",
        "show_activity_panel",
    )
except ImportError:
    # ayon_core not available - standalone mode
    __all__ = (
        "__version__",
        "ActivityPanel",
        "ActivityPanelController",
        "BackendActivityPanelController",
        "FrontendActivityPanelController",
        "show_activity_panel",
    )
