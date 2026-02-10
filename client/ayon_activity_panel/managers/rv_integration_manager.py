"""RV Integration for Activity Panel - listens for AYON source loaded events."""
import json

try:
    import rv.commands

    RV_AVAILABLE = True
except ImportError:
    RV_AVAILABLE = False

from qtpy.QtCore import QTimer

from ayon_core.lib import Logger

log = Logger.get_logger(__name__)


class RVIntegrationManager:
    """Listens for AYON source loaded events and updates activity panel."""

    def __init__(self, activity_panel, debounce_ms=500):
        """Initialize RV integration.
        
        Args:
            activity_panel: Activity panel widget instance.
            debounce_ms: Debounce delay in milliseconds.
        """
        self.activity_panel = activity_panel
        self._bound = False
        self.current_version_id = None
        self._debounce_ms = debounce_ms

        self.update_timer = QTimer()
        self.update_timer.setSingleShot(True)
        self.update_timer.timeout.connect(self._update_for_current_source)

    @staticmethod
    def _read_node_metadata(node):
        """Read minimal metadata from RV node."""
        if not RV_AVAILABLE:
            return None
        try:
            if not rv.commands.propertyExists(f"{node}.ayon.version_id"):
                return None
            return {
                'version_id': rv.commands.getStringProperty(f"{node}.ayon.version_id")[0],
                'project_name': rv.commands.getStringProperty(f"{node}.ayon.project_name")[0]
            }
        except Exception as e:
            log.error(f"Error reading metadata: {e}")
            return None

    def is_active(self):
        """Check if RV integration is active."""
        return RV_AVAILABLE and self._bound

    def get_current_source_group(self):
        """Get current source group (not just source node)."""
        if not RV_AVAILABLE:
            return None
        try:
            view_node = rv.commands.viewNode()
            if not view_node:
                return None

            node_type = rv.commands.nodeType(view_node)
            if node_type == "RVSourceGroup":
                return view_node

            # If viewing a sequence, get the current source from inputs
            if node_type == "RVSequenceGroup":
                inputs = rv.commands.nodeConnections(view_node, False)[0]
                if inputs:
                    # Get first input (could be switchGroup or sourceGroup)
                    first_input = inputs[0]
                    input_type = rv.commands.nodeType(first_input)

                    # If it's a switch group, get its inputs
                    if "switch" in input_type.lower():
                        switch_inputs = rv.commands.nodeConnections(first_input, False)[0]
                        if switch_inputs:
                            source_group = switch_inputs[0]
                            log.debug(f"Got source from switch: {source_group}")
                            return source_group
                    else:
                        log.debug(f"Got source from sequence: {first_input}")
                        return first_input

            # If viewing a source node, get its group
            if "source" in node_type.lower():
                group = rv.commands.nodeGroup(view_node)
                log.debug(f"Got group from source: {group}")
                return group

        except Exception as e:
            log.error(f"get_current_source_group error: {e}")
        return None

    def bind_events(self):
        """Bind to all RV events for activity panel updates."""
        if not RV_AVAILABLE or self._bound:
            return

        try:
            log.info("🟣 [RV INTEGRATION] Binding RV events...")

            # Custom AYON event - fired when assets loaded
            rv.commands.bind(
                "default", "global", "ayon_source_loaded",
                self._on_ayon_source_loaded,
                "Activity Panel: Update on AYON source load"
            )

            # View change events - when switching between sources
            rv.commands.bind(
                "default", "global", "after-graph-view-change",
                self._on_view_change,
                "Activity Panel: Update on view change"
            )

            # Source complete - when source finishes loading
            rv.commands.bind(
                "default", "global", "source-group-complete",
                self._on_source_complete,
                "Activity Panel: Update on source complete"
            )

            # Frame change - update if source changed
            rv.commands.bind(
                "default", "global", "frame-changed",
                self._on_frame_changed,
                "Activity Panel: Update on frame change"
            )

            self._bound = True
            log.info("🟣 [RV INTEGRATION] RV events bound successfully")
        except Exception as e:
            log.warning(f"🟣 [RV INTEGRATION] Failed to bind Activity Panel to RV events: {e}")

    def _on_ayon_source_loaded(self, event):
        """Handle AYON source loaded event - minimal data, auto-build rest."""
        try:
            event_contents = event.contents()
            if not event_contents:
                return

            data = json.loads(event_contents)
            version_id = data.get('version_id')
            project_name = data.get('project_name')

            if not version_id or not project_name:
                log.error("Missing version_id or project_name in event")
                return

            self.activity_panel.set_project(project_name)
            self.activity_panel.set_version(version_id, project_name=project_name)
            self.current_version_id = version_id

        except Exception as e:
            log.error(f"Error handling ayon_source_loaded: {e}")
            import traceback
            traceback.print_exc()

    def _on_view_change(self, event):
        """Handle view change - update panel for new source."""
        self._debounced_update()

    def _on_source_complete(self, event):
        """Handle source complete - update panel."""
        self._debounced_update()

    def _on_frame_changed(self, event):
        """Handle frame change - update if source changed."""
        self._debounced_update()

    def _debounced_update(self):
        """Debounce updates to avoid excessive API calls."""
        self.update_timer.start(self._debounce_ms)

    def _update_for_current_source(self):
        """Update activity panel for current visible source."""
        try:
            current_source = self._get_current_source()
            if not current_source:
                return

            metadata = self._read_node_metadata(current_source)
            if not metadata or not metadata.get('version_id') or not metadata.get('project_name'):
                return

            version_id = metadata['version_id']
            project_name = metadata['project_name']

            if version_id == self.current_version_id:
                return

            self.current_version_id = version_id
            if project_name:
                self.activity_panel.set_project(project_name)
            self.activity_panel.set_version(version_id, project_name=project_name)

        except Exception as e:
            log.error(f"Error updating for current source: {e}")

    @staticmethod
    def _get_current_source():
        """Get current visible source in RV."""
        try:
            sources = rv.commands.sourcesAtFrame(rv.commands.frame())
            source = sources[0] if sources else None
            if source:
                log.debug(f"Current source at frame {rv.commands.frame()}: {source}")
            return source
        except:
            return None
