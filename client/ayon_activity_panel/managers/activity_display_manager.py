"""Activity display manager."""
import base64

from qtpy.QtCore import Qt
from qtpy.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton
from qtpy.QtGui import QPixmap
from qtmaterialsymbols import get_icon

from ayon_core.lib import Logger

from ..workers import ActivityWorker
from ..ui import WebLikeActivityRenderer, AnnotationsDialog

log = Logger.get_logger(__name__)


class ActivityDisplayManager:
    """Manages activity display and updates."""

    def __init__(self, ui, parent, activity_service):
        """Initialize activity display manager.
        
        Args:
            ui: UI instance.
            parent: Parent widget.
            activity_service: Activity service instance.
        """
        self.ui = ui
        self.parent = parent
        self.activity_service = activity_service
        self.worker = None
        self.current_fetch_version = 0
        self.image_cache = {}
        self.activity_images = {}  # Track images per activity: {activity_index: [(file_id, filename, img_data)]}
        self.all_activities = []  # Store all activities
        self.current_filter = 'all'  # 'all', 'comments', 'published', 'checklists'
        self._is_loading_more = False

        # Pagination state
        self._has_previous_page = False
        self._start_cursor = None
        self._last_end_cursor = None

        # Replace QTextBrowser with native renderer
        self.renderer = WebLikeActivityRenderer()
        self.renderer.thumbnail_clicked.connect(self._on_thumbnail_clicked)
        self.renderer.checkbox_changed.connect(self._on_checkbox_changed)

        # Replace in UI
        old_browser = self.ui.textBrowser_activity_panel
        layout = old_browser.parent().layout()
        layout.replaceWidget(old_browser, self.renderer)
        old_browser.deleteLater()

        # Connect scroll event for infinite loading
        scrollbar = self.renderer.verticalScrollBar()
        scrollbar.valueChanged.connect(self._on_scroll)

        # Connect filter buttons
        self.ui.allActivityButton.clicked.connect(lambda: self._on_filter_changed('all'))
        self.ui.commentsButton.clicked.connect(lambda: self._on_filter_changed('comments'))
        self.ui.publishedVersionsButton.clicked.connect(lambda: self._on_filter_changed('published'))
        self.ui.checklistsButton.clicked.connect(lambda: self._on_filter_changed('checklists'))

        # Set icons for filter buttons
        self.ui.allActivityButton.setIcon(get_icon('view_list', color='#99A3B2'))
        self.ui.commentsButton.setIcon(get_icon('comment', color='#99A3B2'))
        self.ui.publishedVersionsButton.setIcon(get_icon('publish', color='#99A3B2'))
        self.ui.checklistsButton.setIcon(get_icon('checklist', color='#99A3B2'))
        self.ui.refreshButton.setIcon(get_icon('refresh', color='#99A3B2'))

        # Style filter buttons using AYON colors
        button_style = """
            QPushButton {
                background-color: #434a56;
                border: 1px solid #373D48;
                border-radius: 0.2em;
                padding: 6px 12px;
                color: #99A3B2;
            }
            QPushButton:hover {
                background-color: #515661;
                color: #F0F2F5;
            }
            QPushButton:checked {
                background-color: rgba(92, 173, 214, .4);
                border: 1px solid rgb(92, 173, 214);
                color: #ffffff;
            }
        """
        self.ui.allActivityButton.setStyleSheet(button_style)
        self.ui.commentsButton.setStyleSheet(button_style)
        self.ui.publishedVersionsButton.setStyleSheet(button_style)
        self.ui.checklistsButton.setStyleSheet(button_style)
        self.ui.refreshButton.setStyleSheet(button_style)

    def fetch_and_display(self, version_id, version_data, project_name, available_statuses):
        """Fetch and display activities.
        
        Args:
            version_id (str): Version ID.
            version_data (dict): Version metadata containing task_id, path, etc.
            project_name (str): Project name.
            available_statuses (list): Available status options.
        """
        if not project_name:
            log.error("No project selected", exc_info=True)
            return

        try:
            self.current_fetch_version += 1
            fetch_id = self.current_fetch_version

            if self.worker and self.worker.isRunning():
                self.worker.cancel()
                self.worker.quit()
                self.worker.wait(100)

            status_colors = {s.get('value', ''): s.get('color', '#ffffff') for s in available_statuses}
            self._status_colors = status_colors

            self.worker = ActivityWorker(
                self.activity_service, version_id, version_data.get('task_id'),
                version_data.get('path'), fetch_id, status_colors, version_data, self.parent
            )
            self.worker.activities_ready.connect(self._render_activities)
            self.worker.image_ready.connect(self._inject_thumbnail)
            self.worker.start()
        except Exception:
            log.error("Failed to fetch and display activities", exc_info=True)

    def _render_activities(self, activities_data, fetch_id):
        """Render activities using native Qt widgets."""
        if fetch_id != self.current_fetch_version:
            return

        self.ui.contentTabWidget.setCurrentIndex(0)

        if not activities_data:
            return

        self.all_activities = activities_data.get('activities', [])
        self._product_name = activities_data.get('product_name', 'Unknown')
        self._current_version = activities_data.get('current_version', 'v000')

        # Extract pagination info
        page_info = activities_data.get('page_info', {})
        self._has_previous_page = page_info.get('hasPreviousPage', False)
        self._start_cursor = page_info.get('startCursor')
        self._last_end_cursor = page_info.get('endCursor')

        self._apply_filter()

    def _on_filter_changed(self, filter_type):
        """Handle filter button clicks."""
        self.current_filter = filter_type

        # Update button states
        self.ui.allActivityButton.setChecked(filter_type == 'all')
        self.ui.commentsButton.setChecked(filter_type == 'comments')
        self.ui.publishedVersionsButton.setChecked(filter_type == 'published')
        self.ui.checklistsButton.setChecked(filter_type == 'checklists')

        self._apply_filter()

    def _apply_filter(self):
        """Apply current filter and render activities."""
        self.renderer.clear()

        if not self.all_activities:
            return

        filtered_activities = self._filter_activities(self.all_activities)
        self._render_filtered_activities(filtered_activities)
        self.renderer.scroll_to_bottom()

    def _filter_activities(self, activities):
        """Filter activities based on current filter."""
        if self.current_filter == 'all':
            return [a for a in activities if a.get('activityType') in ['comment', 'status.change', 'version.publish']]
        elif self.current_filter == 'comments':
            return [a for a in activities if a.get('activityType') == 'comment' and not self._is_checklist(a)]
        elif self.current_filter == 'published':
            return [a for a in activities if a.get('activityType') == 'version.publish']
        elif self.current_filter == 'checklists':
            return [a for a in activities if a.get('activityType') == 'comment' and self._is_checklist(a)]
        return activities

    def _is_checklist(self, activity):
        """Check if activity is a checklist."""
        body = activity.get('body', '')
        import re
        return bool(re.search(r'\*\s*\[[ x]\]', body))

    def _render_filtered_activities(self, activities):
        """Render filtered activities."""
        status_colors = getattr(self, '_status_colors', {})

        for idx, activity in enumerate(activities):
            activity_type = activity.get('activityType')
            author = activity.get('author', {}).get('name', 'Unknown')
            timestamp = self._format_timestamp(activity.get('createdAt', ''))
            activity_id = activity.get('activityId')

            if activity_type == 'status.change':
                data = activity.get('activityData', {})
                if isinstance(data, str):
                    try:
                        import json
                        data = json.loads(data)
                    except:
                        data = {}

                old_status = data.get('oldValue', 'N/A')
                new_status = data.get('newValue', 'N/A')
                old_color = status_colors.get(old_status)
                new_color = status_colors.get(new_status)

                origin = data.get('origin', {})
                origin_type = origin.get('type', '')

                if origin_type == 'task':
                    task_label = origin.get('label', origin.get('name', 'Unknown'))
                    self.renderer.add_task_status_change(
                        author, task_label,
                        old_status, new_status, timestamp,
                        old_color, new_color
                    )
                else:
                    # Extract version-specific data from THIS activity
                    parents = data.get('parents', [])
                    activity_product = parents[1].get('name', 'Unknown') if len(parents) > 1 else getattr(self,
                                                                                                          '_product_name',
                                                                                                          'Unknown')
                    activity_version = origin.get('name', getattr(self, '_current_version', 'v000'))

                    self.renderer.add_status_change(
                        author, activity_product, activity_version,
                        old_status, new_status, timestamp,
                        old_color, new_color
                    )

            elif activity_type == 'version.publish':
                data = activity.get('activityData', {})
                if isinstance(data, str):
                    try:
                        import json
                        data = json.loads(data)
                    except:
                        data = {}

                # Extract from THIS activity
                context = data.get('context', {})
                activity_product = context.get('productName', getattr(self, '_product_name', 'Unknown'))
                origin = data.get('origin', {})
                activity_version = origin.get('name', getattr(self, '_current_version', 'v000'))

                self.renderer.add_version_publish(author, activity_product, activity_version, timestamp)

            elif activity_type == 'comment':
                body = activity.get('body', '')
                if self._is_checklist(activity):
                    checklist_items = self._parse_checklist(body)
                    self.renderer.add_checklist(author, timestamp, checklist_items, activity_index=idx,
                                                activity_id=activity_id, body=body)
                else:
                    tags = self._extract_tags(body)
                    message = self._extract_message(body)
                    self.renderer.add_comment(author, timestamp, message, tags=tags, activity_index=idx)

    def _parse_checklist(self, body):
        """Parse checklist from body."""
        import re
        items = []
        for line in body.split('\n'):
            match = re.match(r'\*\s*\[([x ])\]\s*(.+)', line.strip())
            if match:
                checked = match.group(1).lower() == 'x'
                text = match.group(2).strip()
                items.append((checked, text))
        return items

    def _inject_thumbnail(self, data):
        """Inject thumbnail into comment card."""
        if not isinstance(data, tuple) or len(data) < 4:
            return

        try:
            activity_index, file_id, img_data, filename = data[0], data[1], data[2], data[3]

            # Cache for preview
            self.image_cache[file_id] = img_data

            # Track images per activity for gallery view
            if activity_index not in self.activity_images:
                self.activity_images[activity_index] = []
            self.activity_images[activity_index].append((file_id, filename, img_data))

            # Convert base64 to QPixmap
            pixmap = QPixmap()
            if pixmap.loadFromData(base64.b64decode(img_data)):
                self.renderer.add_thumbnail_to_comment(
                    activity_index, pixmap,
                    tooltip="Click to preview",
                    file_id=file_id,
                    filename=filename
                )
                self.renderer.scroll_to_bottom()
        except Exception:
            log.error(f"Failed to inject thumbnail for file {file_id if 'file_id' in locals() else 'unknown'}",
                      exc_info=True)

    def _on_thumbnail_clicked(self, file_id, activity_index):
        """Handle thumbnail click - open annotations dialog."""
        if activity_index not in self.activity_images:
            return

        images = self.activity_images[activity_index]
        current_index = next((i for i, (fid, _, _) in enumerate(images) if fid == file_id), 0)

        dialog = AnnotationsDialog(images, current_index, self.parent)
        dialog.exec_()

    def _format_timestamp(self, iso_timestamp):
        """Format ISO timestamp to relative time.
        
        Examples:
            - "just now" (< 1 minute)
            - "5m ago" (5 minutes ago)
            - "1hr ago" (1 hour ago, today)
            - "3hrs ago" (3 hours ago, today)
            - "yesterday at 02:30 PM" (previous day)
            - "Jan 15, 2024, 09:45 AM" (older than yesterday)
        """
        if not iso_timestamp:
            return "Unknown time"

        try:
            from datetime import datetime, timezone
            dt = datetime.fromisoformat(iso_timestamp.replace('Z', '+00:00'))
            now = datetime.now(timezone.utc)
            diff = now - dt

            seconds = diff.total_seconds()
            days = diff.days

            if seconds < 60:
                return "just now"
            elif seconds < 3600:
                return f"{int(seconds / 60)}m ago"
            elif days == 0:
                hours = int(seconds / 3600)
                return f"{hours}hr ago" if hours == 1 else f"{hours}hrs ago"
            elif days == 1:
                return f"yesterday{dt.strftime(' at %I:%M %p')}"
            else:
                return dt.strftime("%b %d, %Y, %I:%M %p")
        except:
            return iso_timestamp

    def _extract_tags(self, body):
        """Extract tags from body. Returns list of (tag_text, tag_type) tuples."""
        import re
        tags = []

        # Match [text](type:id) pattern anywhere in body
        pattern = r'\[([^\]]+)\]\(([^:]+):([^\)]+)\)'
        matches = re.findall(pattern, body)

        for text, tag_type, tag_id in matches:
            tags.append((text, tag_type))

        return tags

    def _extract_message(self, body):
        """Convert markdown tags to clickable HTML links with uniform blue color."""
        import re
        import ayon_api

        # Get AYON server URL
        server_url = ayon_api.get_base_url()
        if server_url.endswith('/'):
            server_url = server_url[:-1]

        def replace_tag(match):
            text = match.group(1)
            tag_type = match.group(2)
            tag_id = match.group(3)

            # Uniform blue color for all tags (matching web UI)
            color = '#5b9dd9'

            # User mentions don't have endpoint, just styled text with @ icon
            if tag_type == 'user':
                return f'<span style="color: {color};">@{text}</span>'

            # Add icons for version and task (matching web UI)
            if tag_type == 'version':
                icon = '🔷'  # Diamond icon for versions
                url = f"{server_url}/projects/{self.parent.project_name}/overview?project={self.parent.project_name}&type=version&id={tag_id}"
            elif tag_type == 'task':
                icon = '📋'  # Clipboard icon for tasks
                url = f"{server_url}/projects/{self.parent.project_name}/overview?project={self.parent.project_name}&type=task&id={tag_id}"
            else:
                # Fallback for unknown types
                return f'<span style="color: {color};">{text}</span>'

            return f'<a href="{url}" style="color: {color}; text-decoration: none;">{icon} {text}</a>'

        pattern = r'\[([^\]]+)\]\(([^:]+):([^\)]+)\)'
        message = re.sub(pattern, replace_tag, body)
        return message.strip()

    def _show_image_preview(self, image_data, file_id):
        """Show image preview dialog."""
        dialog = QDialog(self.parent)
        dialog.setWindowTitle(f"Preview - {file_id}")
        dialog.setWindowModality(Qt.ApplicationModal)
        dialog.resize(800, 600)

        layout = QVBoxLayout(dialog)
        label = QLabel()
        label.setAlignment(Qt.AlignCenter)

        pixmap = QPixmap()
        if pixmap.loadFromData(base64.b64decode(image_data)):
            label.setPixmap(pixmap.scaled(750, 550, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            label.setText("Failed to load image")

        layout.addWidget(label)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)

        dialog.exec_()

    def clear(self):
        """Clear activity display and reset state."""
        self.renderer.clear()
        self.activity_images.clear()
        self.all_activities = []

        # Reset pagination state
        self._has_previous_page = False
        self._start_cursor = None
        self._last_end_cursor = None
        self._is_loading_more = False

    def _on_checkbox_changed(self, activity_id, body, item_index, state):
        """Handle checklist checkbox change."""
        try:
            import re
            lines = body.split('\n')
            checkbox_count = 0

            for i, line in enumerate(lines):
                if re.match(r'\*\s*\[[ x]\]', line.strip()):
                    if checkbox_count == item_index:
                        checked = 'x' if state == 2 else ' '
                        lines[i] = re.sub(r'\*\s*\[[ x]\]', f'* [{checked}]', line)
                        break
                    checkbox_count += 1

            new_body = '\n'.join(lines)

            if self.activity_service.update_activity(self.parent.project_name, activity_id, new_body):
                log.info(f"Checklist updated for activity {activity_id}")
                self.parent.refresh()
            else:
                log.error(f"Failed to update checklist for activity {activity_id}", exc_info=True)
        except Exception:
            log.error(f"Exception updating checklist for activity {activity_id}", exc_info=True)

    def _on_scroll(self, value):
        """Load more activities when scrolled to top."""
        scrollbar = self.renderer.verticalScrollBar()

        if value < 100 and not self._is_loading_more and self._has_previous_page:
            self._load_more_activities()

    def _load_more_activities(self):
        """Load older activities using pagination."""
        if self._is_loading_more or not self._has_previous_page:
            return

        self._is_loading_more = True

        from ..api.ayon.ayon_client_api import AyonClient
        client = AyonClient()

        version_id = self.parent.current_version_id
        version_data = self.parent.current_version_data
        project_name = self.parent.project_name

        dcc_mode = version_data and 'version_id' not in version_data
        task_id = version_data.get('task_id') if version_data else None

        entity_ids = [task_id] if dcc_mode and task_id else [version_id]
        if not dcc_mode and task_id and task_id != "N/A":
            entity_ids.append(task_id)

        response = client.get_activities(
            project_name=project_name,
            entity_ids=entity_ids,
            activity_types=['comment', 'status.change', 'version.publish'],
            dcc_mode=dcc_mode,
            last=50,
            before=self._start_cursor
        )

        if response and 'project' in response and response['project']:
            page_info = response['project'].get('activities', {}).get('pageInfo', {})
            edges = response['project'].get('activities', {}).get('edges', [])

            self._has_previous_page = page_info.get('hasPreviousPage', False)
            self._start_cursor = page_info.get('startCursor')

            older_activities = [edge['node'] for edge in edges if edge.get('node')]
            self.all_activities = older_activities + self.all_activities

            scrollbar = self.renderer.verticalScrollBar()
            current_scroll = scrollbar.value()
            self._apply_filter()
            scrollbar.setValue(current_scroll + 200)

        self._is_loading_more = False
