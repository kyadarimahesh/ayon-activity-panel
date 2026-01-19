"""Standalone Activity Panel Widget."""
import logging
import os

from qtpy.QtCore import Signal
from qtpy.QtWidgets import QWidget, QDockWidget, QVBoxLayout

log = logging.getLogger(__name__)

from .ui.generated.activity_panel_ui import Ui_activityCommentDock
from .api.ayon.activity_service import ActivityService
from .api.ayon.version_service import VersionService
from .managers import (
    VersionDetailsManager,
    ActivityDisplayManager,
    RepresentationManager,
    CommentHandler,
    RVActivityPanelIntegration,
    ComparisonManager
)


class ActivityPanel(QWidget):
    """Standalone activity panel widget."""

    version_changed = Signal(str, dict)
    comment_created = Signal(str)

    def __init__(self, project_name=None, parent=None, bind_rv_events=True):
        super().__init__(parent)
        
        log.info(f"🔵 [ACTIVITY PANEL] __init__ called - project_name={project_name}, bind_rv_events={bind_rv_events}")

        self._setup_ui()
        self._init_data()
        self._init_managers()
        self._init_integrations(bind_rv_events)
        self._connect_signals()
        
        # Set initial project from parameter or environment
        if project_name:
            log.info(f"🔵 [ACTIVITY PANEL] Setting project from parameter: {project_name}")
            self.set_project(project_name)
        elif os.getenv("AYON_PROJECT_NAME"):
            env_project = os.getenv("AYON_PROJECT_NAME")
            log.info(f"🔵 [ACTIVITY PANEL] Setting project from env: {env_project}")
            self.set_project(env_project)
        else:
            log.info("🔵 [ACTIVITY PANEL] No project set during init")

    def _setup_ui(self):
        """Setup UI components."""
        self.ui = Ui_activityCommentDock()
        temp_dock = QDockWidget()
        temp_dock.setObjectName("ActivityPanelDock")
        self.ui.setupUi(temp_dock)
        content_widget = self.ui.activityCommentWidget
        content_widget.setParent(self)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(content_widget)

        self.ui.mainSplitter.setSizes([100, 500, 150])

    def _init_data(self):
        """Initialize data attributes."""
        self.project_name = None
        self.current_version_id = None
        self.current_version_data = None
        self.available_statuses = []

    def _init_managers(self):
        """Initialize manager instances."""
        self.activity_service = ActivityService()
        self.version_service = VersionService()
        self.comment_handler = CommentHandler(self)
        self.comparison_mgr = ComparisonManager(self)

        self.version_details_mgr = VersionDetailsManager(self.ui, self)
        self.activity_display_mgr = ActivityDisplayManager(self.ui, self, self.activity_service)
        self.representation_mgr = RepresentationManager(self.ui, self)

    def _init_integrations(self, bind_rv_events):
        """Initialize RV integration."""
        if bind_rv_events:
            log.info("🔵 [ACTIVITY PANEL] Creating RV integration with bind_rv_events=True")
            self.rv_integration = RVActivityPanelIntegration(self)
        else:
            log.info("🔵 [ACTIVITY PANEL] RV integration disabled (bind_rv_events=False)")
            self.rv_integration = None

    def enable_rv_events(self):
        """Manually enable RV event binding after session is stable."""
        log.info("🔵 [ACTIVITY PANEL] enable_rv_events called")
        if self.rv_integration and not self.rv_integration._bound:
            log.info("🔵 [ACTIVITY PANEL] Binding RV events and triggering initial update")
            self.rv_integration.bind_events()
            # Trigger initial update for current source
            self.rv_integration._update_for_current_source()
        elif not self.rv_integration:
            log.warning("🔵 [ACTIVITY PANEL] No RV integration to enable")
        elif self.rv_integration._bound:
            log.info("🔵 [ACTIVITY PANEL] RV events already bound")

    def _connect_signals(self):
        """Connect UI signals."""
        self.ui.pushButton_comment.clicked.connect(self._on_comment_clicked)
        self.ui.statusComboBox.currentTextChanged.connect(self._on_status_changed)
        self.ui.versionComboBox.currentTextChanged.connect(self._on_version_changed)
        self.ui.textBrowser_activity_panel.anchorClicked.connect(
            self.activity_display_mgr.handle_anchor_click
        )

    # Public API
    def set_project(self, project_name: str):
        """Set current project and fetch statuses."""
        log.info(f"🟢 [WIDGET] set_project called: {project_name}")
        log.info(f"🟢 [WIDGET] Current available_statuses before: {len(self.available_statuses)}")
        
        self.project_name = project_name
        
        # Auto-fetch statuses when project is set
        if project_name:
            log.info(f"🟢 [WIDGET] Fetching statuses for project: {project_name}")
            statuses = self.version_service.get_version_statuses(project_name)
            log.info(f"🟢 [WIDGET] Fetched {len(statuses)} statuses: {statuses}")
            if statuses:
                self.set_available_statuses(statuses)
                log.info(f"🟢 [WIDGET] Statuses set successfully")
            else:
                log.error(f"🟢 [WIDGET] No statuses returned!")
        
        log.info(f"🟢 [WIDGET] Final available_statuses: {len(self.available_statuses)}")

    def set_version(self, version_id: str, version_data: dict):
        """Set current version and update UI."""
        if not version_id or not version_data:
            log.warning("Missing data, clearing panel")
            self.clear()
            return

        # Auto-set project from version_data if available
        project_name = version_data.get('project_name')
        if project_name and project_name != self.project_name:
            self.project_name = project_name
            statuses = self.version_service.get_version_statuses(project_name)
            if statuses:
                self.available_statuses = statuses

        # Lazy fetch statuses if still missing
        if not self.available_statuses and self.project_name:
            statuses = self.version_service.get_version_statuses(self.project_name)
            if statuses:
                self.available_statuses = statuses

        self.current_version_id = version_id
        self.current_version_data = version_data
        
        self.version_details_mgr.update(version_data, self.available_statuses)
        self.representation_mgr.update_tab(version_data)

        self.activity_display_mgr.fetch_and_display(
            version_id, version_data, self.project_name, self.available_statuses
        )

        self.version_changed.emit(version_id, version_data)

    def set_available_statuses(self, statuses: list):
        """Set available statuses."""
        self.available_statuses = statuses
        if self.current_version_data:
            self.version_details_mgr.update(self.current_version_data, statuses)

    def refresh(self):
        """Refresh current version activities."""
        if self.current_version_id and self.current_version_data:
            self.activity_display_mgr.fetch_and_display(
                self.current_version_id, self.current_version_data,
                self.project_name, self.available_statuses
            )

    def clear(self):
        """Clear all UI components."""
        self.activity_display_mgr.clear()
        self.version_details_mgr.clear()
        self.ui.textEdit_comment.clear()
        self.current_version_id = None
        self.current_version_data = None

    # Event handlers
    def _on_comment_clicked(self):
        """Handle comment button click."""
        if not self.current_version_id or not self.project_name or not self.current_version_data:
            return

        message = self.ui.textEdit_comment.toPlainText().strip()

        success = self.comment_handler.create_comment(
            message=message,
            version_data=self.current_version_data,
            activity_service=self.activity_service,
            project_name=self.project_name,
            refresh_callback=self.refresh
        )

        if success:
            self.ui.textEdit_comment.clear()
            self.comment_created.emit(self.current_version_id)

    def _on_status_changed(self, new_status: str):
        """Handle status change."""
        if not self.current_version_data or not new_status:
            return

        version_id = self.current_version_data.get('version_id', '')
        if not version_id or not self.project_name:
            return

        success = self.version_service.update_version_status(
            self.project_name, version_id, new_status
        )

        if success:
            self.current_version_data['version_status'] = new_status
            self.refresh()

    def _on_version_changed(self, new_version: str):
        """Handle version change from dropdown."""

        if not self.current_version_data or not new_version:
            log.warning("Version switch: Missing current_version_data or new_version")
            return

        current_version = self.current_version_data.get('current_version', '')

        if current_version == new_version:
            log.debug("Version switch: Same version, skipping")
            return

        # Get current source IMMEDIATELY before any changes
        current_source = None
        if self.rv_integration and self.rv_integration.is_active():
            current_source = self.rv_integration.get_current_source_group()

        # Find version data from all_product_versions
        all_product_versions = self.current_version_data.get('all_product_versions', [])

        if not all_product_versions:
            log.error("Version switch: No all_product_versions available")
            return

        selected_version_data = None
        for version in all_product_versions:
            version_name = f"v{version.get('version', 1):03d}"
            if version_name == new_version:
                selected_version_data = version
                break

        if not selected_version_data:
            log.error(f"Version switch: Could not find version data for: {new_version}")
            return

        # Build updated version data
        updated_version_data = self._build_version_data_from_node(selected_version_data)
        updated_version_data['all_product_versions'] = all_product_versions

        # Check if in RV mode
        is_rv_mode = self.rv_integration and self.rv_integration.is_active()
        log.debug(f"RV mode active: {is_rv_mode}")

        if is_rv_mode:
            # Use captured source from beginning of function
            log.debug(f"Creating comparison stack (will load new version in RV)")
            log.debug(f"Current source: {current_source}")
            self.comparison_mgr.create_comparison_stack(
                self.current_version_data,
                updated_version_data,
                set_view_to_new=True,
                existing_source=current_source
            )

        # Update activity panel to new version
        self.set_version(updated_version_data['version_id'], updated_version_data)

    def _build_version_data_from_node(self, version_node):
        """Build version_data dict from version node."""
        # Extract representations
        representations = []
        rep_edges = version_node.get('representations', {}).get('edges', [])
        for edge in rep_edges:
            node = edge.get('node', {})
            if node:
                representations.append({
                    'id': node.get('id'),
                    'name': node.get('name'),
                    'path': node.get('attrib', {}).get('path', '')
                })

        # Build versions list from all_product_versions if available
        versions = self.current_version_data.get('versions', [])
        product_name = self.current_version_data.get('product_name', 'Unknown')

        return {
            'version_id': version_node.get('id', ''),
            'task_id': version_node.get('taskId', ''),
            'product_name': product_name,
            'path': self.current_version_data.get('path', 'N/A'),
            'current_version': f"v{version_node.get('version', 1):03d}",
            'versions': versions,
            'version_status': version_node.get('status', 'N/A'),
            'author': version_node.get('author', 'N/A'),
            'representations': representations,
            'current_representation_path': representations[0].get('path', '') if representations else ''
        }
