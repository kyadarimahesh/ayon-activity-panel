"""Manager modules for Activity Panel."""

from .version_details_manager import VersionDetailsManager
from .activity_display_manager import ActivityDisplayManager
from .representation_manager import RepresentationManager
from .comment_manager import CommentHandler
from .rv_integration_manager import RVActivityPanelIntegration
from .comparison_manager import ComparisonManager

__all__ = [
    "VersionDetailsManager",
    "ActivityDisplayManager",
    "RepresentationManager",
    "CommentHandler",
    "RVActivityPanelIntegration",
    "ComparisonManager"
]
