"""Activity display manager."""
import logging

from qtpy.QtCore import Qt
from qtpy.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton
from qtpy.QtGui import QPixmap

from ..workers import ActivityWorker

log = logging.getLogger(__name__)


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
        self.saved_content = ""
        self.saved_scroll_position = 0
    
    def fetch_and_display(self, version_id, row_data, project_name, available_statuses):
        """Fetch and display activities.
        
        Args:
            version_id (str): Version ID.
            row_data (dict): Version data.
            project_name (str): Project name.
            available_statuses (list): Available status options.
        """
        if not project_name:
            self.ui.textBrowser_activity_panel.setHtml("<p style='color:red;'>Error: No project selected</p>")
            return
        
        self.current_fetch_version += 1
        fetch_id = self.current_fetch_version
        
        if self.worker and self.worker.isRunning():
            self.worker.cancel()
            self.worker.quit()
            self.worker.wait(100)
        
        status_colors = {s.get('value', ''): s.get('color', '#ffffff') for s in available_statuses}
        
        self.worker = ActivityWorker(
            self.activity_service, version_id, row_data.get('task_id'),
            row_data.get('path'), fetch_id, status_colors, self.parent
        )
        self.worker.text_ready.connect(self._update_ui)
        self.worker.image_ready.connect(self._update_image)
        self.worker.start()
    
    def _update_ui(self, activities_html, fetch_id):
        if fetch_id != self.current_fetch_version:
            return
        
        self.ui.contentTabWidget.setCurrentIndex(0)
        
        if activities_html and activities_html.strip():
            self.ui.textBrowser_activity_panel.setHtml(activities_html)
        else:
            self.ui.textBrowser_activity_panel.setHtml("<p style='color:gray;'>No activities found for this version</p>")
        
        scrollbar = self.ui.textBrowser_activity_panel.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def _update_image(self, data):
        if isinstance(data, tuple) and len(data) >= 2:
            file_id, img_tag = data[0], data[1]
            if len(data) >= 3:
                self.image_cache[file_id] = data[2]
            
            current_html = self.ui.textBrowser_activity_panel.toHtml()
            loading_id = f'loading_{file_id}'
            
            if loading_id in current_html:
                import re
                pattern = f'<a name="{loading_id}"></a>.*?oading.*?</span>'
                match = re.search(pattern, current_html, flags=re.DOTALL)
                
                if match:
                    updated_html = current_html.replace(match.group(0), img_tag)
                    self.ui.textBrowser_activity_panel.setHtml(updated_html)
                    
                    scrollbar = self.ui.textBrowser_activity_panel.verticalScrollBar()
                    scrollbar.setValue(scrollbar.maximum())
    
    def handle_anchor_click(self, url):
        """Handle anchor clicks in activity panel."""
        url_str = url.toString()
        if url_str.startswith("preview:"):
            parts = url_str.split(":", 2)
            if len(parts) >= 3:
                file_id, filename = parts[1], parts[2]
                if file_id in self.image_cache:
                    self._show_image_preview(self.image_cache[file_id], filename)
    
    def _show_image_preview(self, image_data, filename):
        import base64
        
        text_browser = self.ui.textBrowser_activity_panel
        self.saved_content = text_browser.toHtml()
        self.saved_scroll_position = text_browser.verticalScrollBar().value()
        
        dialog = QDialog(self.parent)
        dialog.setWindowTitle(f"Preview - {filename}")
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
        
        text_browser.setHtml(self.saved_content)
        text_browser.verticalScrollBar().setValue(self.saved_scroll_position)
    
    def clear(self):
        """Clear activity display."""
        self.ui.textBrowser_activity_panel.clear()
