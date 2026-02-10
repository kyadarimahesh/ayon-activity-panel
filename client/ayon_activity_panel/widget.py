"""Standalone Activity Panel Widget.

UI-only widget following AYON architecture pattern.
All business logic is delegated to the controller via abstract interfaces.
"""
from __future__ import annotations

from typing import Optional, Any, Union, TYPE_CHECKING

from qtpy import QtWidgets, QtCore

from ayon_core.lib import Logger
from ayon_core.pipeline import get_current_project_name

from .ui import ActivityPanelUI
from .abstract import BackendActivityPanelController, FrontendActivityPanelController
from .control import ActivityPanelController
from .handlers import ScreenshotHandler, ReviewHandler

if TYPE_CHECKING:
    # Combined interface type for type checking
    ControllerType = Union[BackendActivityPanelController, FrontendActivityPanelController]

log = Logger.get_logger(__name__)


class ActivityPanel(QtWidgets.QWidget):
    """Standalone activity panel widget.

    UI-only implementation - all business logic delegated to controller.
    Accepts any controller implementing Backend and Frontend interfaces.
    Displays version activities, comments, and status changes.
    Supports both version mode and DCC task mode.
    """

    # Signals for external listeners
    version_changed = QtCore.Signal(str, dict)
    comment_created = QtCore.Signal(str)

    def __init__(
            self,
            controller: Optional["ControllerType"] = None,
            project_name: Optional[str] = None,
            parent: Optional[QtWidgets.QWidget] = None,
            bind_rv_events: bool = True,
            settings: Optional[dict[str, Any]] = None
    ):
        super().__init__(parent)

        if controller is None:
            controller = ActivityPanelController()

        self._controller = controller
        self._settings = settings or {}

        self._setup_ui()
        self._init_timers()
        self._init_managers()
        self._init_integrations(bind_rv_events)
        self._connect_signals()
        self._register_controller_events()

        if project_name:
            self.set_project(project_name)
        else:
            self._try_auto_set_project()

    # -------------------------------------------------------------------------
    # Setup Methods
    # -------------------------------------------------------------------------
    def _setup_ui(self):
        """Setup UI components."""
        self.ui = ActivityPanelUI()
        self.ui.setupUi(self)

        self._restore_splitter_sizes()
        self.ui.mainSplitter.splitterMoved.connect(self._save_splitter_sizes)

        # Replace QTextEdit with custom CommentTextEdit for @ mentions
        from .ui.mention_completer import CommentTextEdit
        old_text_edit = self.ui.textEdit_comment
        new_text_edit = CommentTextEdit(old_text_edit.parent())
        new_text_edit.setObjectName("textEdit_comment")
        new_text_edit.setPlaceholderText(old_text_edit.placeholderText())
        layout = old_text_edit.parent().layout()
        layout.replaceWidget(old_text_edit, new_text_edit)
        old_text_edit.deleteLater()
        self.ui.textEdit_comment = new_text_edit

        # Add screenshot and review buttons
        from qtmaterialsymbols import get_icon

        self.screenshot_btn = QtWidgets.QPushButton()
        self.screenshot_btn.setIcon(get_icon('photo_camera', color='#99A3B2'))
        self.screenshot_btn.setToolTip("Left-click: Capture | Right-click: Preview")
        self.screenshot_btn.setFixedSize(45, 32)
        self.screenshot_btn.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.ui.buttonLayout.insertWidget(0, self.screenshot_btn)

        self.review_btn = QtWidgets.QPushButton()
        self.review_btn.setIcon(get_icon('play_circle', color='#99A3B2'))
        self.review_btn.setToolTip("Open in RV for Review")
        self.review_btn.setFixedSize(45, 32)
        self.ui.buttonLayout.insertWidget(0, self.review_btn)

        # Initialize handlers
        self.screenshot_handler = ScreenshotHandler(self, self.screenshot_btn)
        self.review_handler = ReviewHandler(self)

        # Connect button signals
        self.screenshot_btn.clicked.connect(self.screenshot_handler.launch_capture)
        self.screenshot_btn.customContextMenuRequested.connect(
            self.screenshot_handler.show_all_preview
        )
        self.review_btn.clicked.connect(self.review_handler.launch_review)

    def _init_timers(self):
        """Initialize timers."""
        refresh_interval = self._settings.get('auto_refresh_interval_ms', 300000)
        self._refresh_timer = QtCore.QTimer()
        self._refresh_timer.timeout.connect(self._on_auto_refresh)
        self._refresh_timer.start(refresh_interval)

    def _init_managers(self):
        """Initialize manager instances."""
        from .managers import (
            VersionDetailsManager,
            ActivityDisplayManager,
            RepresentationManager,
            CommentManager,
            ComparisonManager
        )

        self.comment_manager = CommentManager(self)
        self.comparison_manager = ComparisonManager(self)
        self.version_details_mgr = VersionDetailsManager(self.ui, self)
        self.activity_display_mgr = ActivityDisplayManager(
            self.ui, self, self._controller.activity_service
        )
        self.representation_mgr = RepresentationManager(self.ui, self)

    def _init_integrations(self, bind_rv_events: bool):
        """Initialize RV integration."""
        from .managers import RVIntegrationManager

        enable_rv = self._settings.get('enable_rv_integration', True)
        debounce_ms = self._settings.get('debounce_delay_ms', 500)

        if bind_rv_events and enable_rv:
            self.rv_integration_manager = RVIntegrationManager(
                self, debounce_ms=debounce_ms
            )
        else:
            self.rv_integration_manager = None

    def _connect_signals(self):
        """Connect UI signals to handlers."""
        self.ui.pushButton_comment.clicked.connect(self._on_comment_clicked)
        self.ui.statusComboBox.currentTextChanged.connect(self._on_status_changed)
        self.ui.versionComboBox.currentTextChanged.connect(self._on_version_changed)
        self.ui.refreshButton.clicked.connect(self._on_refresh_clicked)

        if self.parent():
            self.parent().destroyed.connect(self._on_parent_destroyed)

    def _register_controller_events(self):
        """Register for controller events."""
        self._controller.register_event_callback(
            "version.changed", self._on_controller_version_changed
        )
        self._controller.register_event_callback(
            "version.refreshed", self._on_controller_version_refreshed
        )
        self._controller.register_event_callback(
            "version.cleared", self._on_controller_cleared
        )

    def _try_auto_set_project(self):
        """Try to auto-set project from current context."""
        try:
            context_project = get_current_project_name()
            if context_project:
                self.set_project(context_project)
        except Exception:
            pass

    # -------------------------------------------------------------------------
    # Public API
    # -------------------------------------------------------------------------
    def set_project(self, project_name: str):
        """Set current project."""
        self._controller.set_project(project_name)
        self.ui.textEdit_comment.fetch_users(project_name)

    def set_version(
            self,
            version_id: str,
            version_data: Optional[dict] = None,
            project_name: Optional[str] = None
    ):
        """Set current version and update UI."""
        self._controller.set_version(version_id, version_data, project_name)

    def refresh(self):
        """Refresh current version data and activities."""
        self._controller.refresh()

    def clear(self):
        """Clear all UI components."""
        self._controller.clear()

    def enable_rv_events(self):
        """Manually enable RV event binding after session is stable."""
        if self.rv_integration_manager and not self.rv_integration_manager._bound:
            self.rv_integration_manager.bind_events()
            self.rv_integration_manager._update_for_current_source()

    def set_available_statuses(self, statuses: list[dict[str, Any]]):
        """Set available statuses (for external code compatibility)."""
        self._controller._available_statuses = statuses
        version_data = self._controller.get_current_version_data()
        if version_data:
            dcc_mode = 'version_id' not in version_data
            self.version_details_mgr.update(version_data, statuses, dcc_mode)

    # -------------------------------------------------------------------------
    # Properties (delegate to controller)
    # -------------------------------------------------------------------------
    @property
    def project_name(self) -> Optional[str]:
        return self._controller.get_project_name()

    @property
    def current_version_id(self) -> Optional[str]:
        return self._controller.get_current_version_id()

    @property
    def current_version_data(self) -> Optional[dict[str, Any]]:
        return self._controller.get_current_version_data()

    @property
    def available_statuses(self) -> list[dict[str, Any]]:
        return self._controller.get_available_statuses()

    # -------------------------------------------------------------------------
    # Controller Event Handlers
    # -------------------------------------------------------------------------
    def _on_controller_version_changed(self, event: dict):
        """Handle version changed event from controller."""
        version_id = event.get("version_id")
        version_data = event.get("version_data")
        dcc_mode = event.get("dcc_mode", False)
        statuses = self._controller.get_available_statuses()

        self.version_details_mgr.update(version_data, statuses, dcc_mode)
        self.representation_mgr.update_tab(version_data)
        self.activity_display_mgr.fetch_and_display(
            version_id, version_data, self._controller.get_project_name(), statuses
        )
        self.version_changed.emit(version_id, version_data)

    def _on_controller_version_refreshed(self, event: dict):
        """Handle version refreshed event from controller."""
        version_data = event.get("version_data")
        version_id = event.get("version_id")
        statuses = self._controller.get_available_statuses()

        if version_data:
            dcc_mode = 'version_id' not in version_data
            self.version_details_mgr.update(version_data, statuses, dcc_mode)
            self.representation_mgr.update_tab(version_data)

        self.activity_display_mgr.fetch_and_display(
            version_id, version_data, self._controller.get_project_name(), statuses
        )

    def _on_controller_cleared(self, event: dict):
        """Handle cleared event from controller."""
        self.activity_display_mgr.clear()
        self.version_details_mgr.clear()
        self.ui.textEdit_comment.clear()

    # -------------------------------------------------------------------------
    # UI Event Handlers
    # -------------------------------------------------------------------------
    def _on_refresh_clicked(self):
        """Handle manual refresh button click."""
        self._controller.refresh()

    def _on_auto_refresh(self):
        """Handle auto-refresh timer."""
        if self._controller.get_current_version_id():
            self._controller.refresh()

    def _on_comment_clicked(self):
        """Handle comment button click - delegate to CommentManager."""
        version_data = self._controller.get_current_version_data()
        project_name = self._controller.get_project_name()

        if not version_data or not project_name:
            return

        message = self._get_formatted_comment()
        if not message:
            return

        # Delegate everything to CommentManager (handles RV annotations, API, cleanup)
        self.comment_manager.create_comment(
            message=message,
            version_data=version_data,
            activity_service=self._controller.activity_service,
            project_name=project_name,
            refresh_callback=self._controller.refresh,
            screenshot_paths=self.screenshot_handler.get_screenshot_paths(),
            on_success=self._on_comment_success
        )

    def _get_formatted_comment(self) -> str:
        """Get comment text with @mentions formatted."""
        import re
        message = self.ui.textEdit_comment.toPlainText().strip()
        if not message:
            return ""
        return re.sub(r'@(\w+)', lambda m: f"[{m.group(1)}](user:{m.group(1)})", message)

    def _on_comment_success(self):
        """Cleanup after successful comment - called by CommentManager."""
        self.ui.textEdit_comment.clear()
        self.screenshot_handler.clear_screenshots()
        version_id = self._controller.get_current_version_id()
        if version_id:
            self.comment_created.emit(version_id)

    def _on_status_changed(self, new_status: str):
        """Handle status change from UI."""
        version_data = self._controller.get_current_version_data()
        if not version_data or not new_status:
            return

        dcc_mode = 'version_id' not in version_data
        entity_id = version_data.get('task_id' if dcc_mode else 'version_id', '')

        if entity_id and self._controller.update_version_status(entity_id, new_status, is_task=dcc_mode):
            self._controller.refresh()

    def _on_version_changed(self, new_version: str):
        """Handle version change from dropdown."""
        version_data = self._controller.get_current_version_data()
        if not version_data or not new_version:
            return

        if version_data.get('current_version', '') == new_version:
            return

        # Find and build new version data
        all_versions = version_data.get('all_product_versions', [])
        selected = next(
            (v for v in all_versions if f"v{v.get('version', 1):03d}" == new_version),
            None
        )

        if not selected:
            log.error(f"Could not find version data for: {new_version}")
            return

        updated_data = self._controller.build_version_data_from_node(selected, version_data)
        updated_data['all_product_versions'] = all_versions

        # Handle RV comparison if active
        if self.rv_integration_manager and self.rv_integration_manager.is_active():
            current_source = self.rv_integration_manager.get_current_source_group()
            self.comparison_manager.create_comparison_stack(
                version_data, updated_data, set_view_to_new=True, existing_source=current_source
            )

        self._controller.set_version(updated_data['version_id'], updated_data)

    def _on_parent_destroyed(self):
        """Handle parent widget destruction."""
        self.close()

    # -------------------------------------------------------------------------
    # Settings & Lifecycle
    # -------------------------------------------------------------------------
    def _save_splitter_sizes(self) -> None:
        settings = QtCore.QSettings("AYON", "ActivityPanel")
        settings.setValue("mainSplitter/sizes", self.ui.mainSplitter.sizes())

    def _restore_splitter_sizes(self) -> None:
        settings = QtCore.QSettings("AYON", "ActivityPanel")
        sizes = settings.value("mainSplitter/sizes")
        if sizes:
            self.ui.mainSplitter.setSizes([int(s) for s in sizes])

    def closeEvent(self, event):
        """Handle close event - cleanup."""
        self._save_splitter_sizes()
        if hasattr(self, '_refresh_timer'):
            self._refresh_timer.stop()
        super().closeEvent(event)
