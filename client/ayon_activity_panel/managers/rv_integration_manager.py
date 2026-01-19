"""RV Integration for Activity Panel - listens for AYON source loaded events."""
import logging
import json

try:
    import rv.commands
    RV_AVAILABLE = True
except ImportError:
    RV_AVAILABLE = False

from qtpy.QtCore import QTimer

log = logging.getLogger(__name__)


class RVActivityPanelIntegration:
    """Listens for AYON source loaded events and updates activity panel."""

    def __init__(self, activity_panel):
        """Initialize RV integration.
        
        Args:
            activity_panel: Activity panel widget instance.
        """
        self.activity_panel = activity_panel
        self._bound = False
        self.current_version_id = None

        # Debounce timer for updates
        self.update_timer = QTimer()
        self.update_timer.setSingleShot(True)
        self.update_timer.timeout.connect(self._update_for_current_source)

    @staticmethod
    def _read_node_metadata(node):
        """Read version metadata from RV node properties."""
        if not RV_AVAILABLE:
            return None

        try:
            import json

            if not rv.commands.propertyExists(f"{node}.ayon.version_id"):
                return None

            def get_prop(key):
                prop = f"{node}.ayon.{key}"
                if rv.commands.propertyExists(prop):
                    values = rv.commands.getStringProperty(prop)
                    return values[0] if values else None
                return None

            def get_json_prop(key):
                """Get property and parse as JSON if it's a string."""
                value = get_prop(key)
                if value:
                    try:
                        return json.loads(value)
                    except:
                        return value
                return None

            metadata = {
                'version_id': get_prop('version_id'),
                'representation_id': get_prop('representation_id'),
                'file_path': get_prop('file_path'),
                'product_id': get_prop('product_id'),
                'product_name': get_prop('product_name'),
                'task_id': get_prop('task_id'),
                'path': get_prop('folder_path'),
                'current_version': get_prop('version_name'),
                'version_status': get_prop('version_status'),
                'author': get_prop('author'),
                'project_name': get_prop('project_name'),
                'versions': get_json_prop('versions'),
                'all_product_versions': get_json_prop('all_product_versions'),
                'representations': get_json_prop('representations'),
                'current_representation_path': get_prop('file_path')
            }

            return metadata
        except Exception as e:
            log.error(f"Error reading metadata: {e}")
            import traceback
            traceback.print_exc()
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

            # Stack navigation - ( and ) keys
            rv.commands.bind(
                "default", "global", "key-down--(",
                self._on_stack_backward,
                "Activity Panel: Update on stack backward"
            )
            rv.commands.bind(
                "default", "global", "key-down--)",
                self._on_stack_forward,
                "Activity Panel: Update on stack forward"
            )

            self._bound = True
            log.info("🟣 [RV INTEGRATION] RV events bound successfully")
        except Exception as e:
            log.warning(f"🟣 [RV INTEGRATION] Failed to bind Activity Panel to RV events: {e}")

    def _on_ayon_source_loaded(self, event):
        """Handle AYON source loaded event - register source mapping."""
        try:
            event_contents = event.contents()
            if not event_contents:
                return

            data = json.loads(event_contents)
            version_id = data.get('version_id')

            if not version_id:
                log.error("No version_id in event data")
                return

            # Build row_data from event
            row_data = {
                'version_id': version_id,
                'task_id': data.get('task_id'),
                'product_id': data.get('product_id'),
                'product_name': data.get('product_name'),
                'path': data.get('path'),
                'current_version': data.get('current_version'),
                'versions': data.get('versions', []),
                'all_product_versions': data.get('all_product_versions', []),
                'version_status': data.get('version_status'),
                'author': data.get('author'),
                'representations': data.get('representations', []),
                'current_representation_path': data.get('current_representation_path', '')
            }

            # Update panel immediately for first load
            project_name = data.get('project_name')
            if project_name:
                self.activity_panel.set_project(project_name)

            self.activity_panel.set_version(version_id, row_data)
            self.current_version_id = version_id

        except Exception as e:
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

    def _on_stack_backward(self, event):
        """Handle stack backward navigation (( key)."""
        self.current_version_id = None  # Force update
        self._debounced_update()

    def _on_stack_forward(self, event):
        """Handle stack forward navigation () key)."""
        self.current_version_id = None  # Force update
        self._debounced_update()

    def _debounced_update(self):
        """Debounce updates to avoid excessive API calls."""
        self.update_timer.start(500)  # 500 ms debounce

    def _update_for_current_source(self):
        """Update activity panel for current visible source."""
        try:
            log.info("🟣 [RV ACTIVITY PANEL] _update_for_current_source triggered")
            
            current_source = self._get_current_source()
            if not current_source:
                log.info("🟣 [RV ACTIVITY PANEL] No current source found")
                return

            log.info(f"🟣 [RV ACTIVITY PANEL] Reading metadata from node: {current_source}")
            
            # Read metadata directly from node
            metadata = self._read_node_metadata(current_source)
            if not metadata or not metadata.get('version_id'):
                log.info("🟣 [RV ACTIVITY PANEL] No metadata or version_id on node")
                return

            version_id = metadata['version_id']
            project_name = metadata.get('project_name')
            
            log.info(f"🟣 [RV ACTIVITY PANEL] Metadata read:")
            log.info(f"   - version_id: {version_id}")
            log.info(f"   - project_name: {project_name}")
            log.info(f"   - version_status: {metadata.get('version_status')}")

            # Only update if version changed
            if version_id == self.current_version_id:
                log.info("🟣 [RV ACTIVITY PANEL] Same version as before, skipping update")
                return

            self.current_version_id = version_id

            # Use metadata as row_data
            row_data = metadata

            # Set project if available
            if project_name:
                log.info(f"🟣 [RV ACTIVITY PANEL] Calling set_project({project_name})")
                log.info(f"🟣 [RV ACTIVITY PANEL] Current panel.available_statuses: {len(self.activity_panel.available_statuses)}")
                self.activity_panel.set_project(project_name)
                log.info(f"🟣 [RV ACTIVITY PANEL] After set_project, panel.available_statuses: {len(self.activity_panel.available_statuses)}")

            log.info(f"🟣 [RV ACTIVITY PANEL] Calling set_version({version_id})")
            self.activity_panel.set_version(version_id, row_data)
            log.info(f"🟣 [RV ACTIVITY PANEL] set_version completed")

        except Exception as e:
            log.error(f"🟣 [RV ACTIVITY PANEL] Error: {e}")
            import traceback
            traceback.print_exc()

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

    def on_version_dropdown_changed(self, new_version_name, all_product_versions, versions_list):
        """Handle version dropdown change - update node metadata.
        
        Args:
            new_version_name (str): New version name.
            all_product_versions (list): All product versions.
            versions_list (list): List of version names.
        """
        log.debug(f"Version dropdown changed to: {new_version_name}")

        if not RV_AVAILABLE or not all_product_versions:
            log.warning("RV not available or no versions")
            return

        try:
            current_source = self._get_current_source()
            if not current_source:
                log.error("No current source")
                return

            # Find new version data by name
            new_version_data = None
            for version in all_product_versions:
                version_name = version.get('name') or f"v{version.get('version', 0):03d}"
                if version_name == new_version_name:
                    new_version_data = version
                    break

            if not new_version_data:
                log.error(f"Version data not found for: {new_version_name}")
                return

            # Update node metadata including versions arrays
            self._update_node_metadata(current_source, new_version_data, all_product_versions, versions_list)

            # Update current version tracking
            self.current_version_id = new_version_data.get('id')

        except Exception as e:
            log.error(f"RV Integration Error: {e}")
            import traceback
            traceback.print_exc()

    @staticmethod
    def _update_node_metadata(node, version_data, all_product_versions, versions_list):
        """Update RV node metadata with new version data."""
        if not RV_AVAILABLE:
            return

        import json

        metadata = {
            'version_id': version_data.get('id'),
            'version_name': version_data.get('name'),
            'version_status': version_data.get('status'),
            'author': version_data.get('author'),
            'versions': json.dumps(versions_list),
            'all_product_versions': json.dumps(all_product_versions)
        }

        for key, value in metadata.items():
            if value:
                prop = f"{node}.ayon.{key}"
                if not rv.commands.propertyExists(prop):
                    rv.commands.newProperty(prop, rv.commands.StringType, 1)
                rv.commands.setStringProperty(prop, [value], True)
