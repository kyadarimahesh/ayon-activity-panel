from qtpy.QtCore import QThread, Signal


class ActivityWorker(QThread):
    """Background worker for fetching activities"""
    
    text_ready = Signal(str, int)
    image_ready = Signal(tuple)
    
    def __init__(self, activity_service, version_id, task_id, path, fetch_id, status_colors, parent=None):
        super().__init__(parent)
        self.activity_service = activity_service
        self.version_id = version_id
        self.task_id = task_id
        self.path = path
        self.fetch_id = fetch_id
        self.status_colors = status_colors
        self._cancelled = False
    
    def cancel(self):
        self._cancelled = True
    
    def run(self):
        if self._cancelled:
            return
        
        try:
            project_name = self.parent().project_name if self.parent() else None
            
            if not project_name:
                self.text_ready.emit("<p style='color:red;'>Error: No project name</p>", self.fetch_id)
                return
            
            def update_callback(data, event_type):
                if self._cancelled:
                    return
                
                if event_type == "text_ready":
                    self.text_ready.emit(data, self.fetch_id)
                elif event_type == "image_ready":
                    self.image_ready.emit(data)
            
            self.activity_service.process_version_activities(
                project_name, 
                self.version_id,
                task_id=self.task_id,
                path=self.path,
                status_colors=self.status_colors,
                update_callback=update_callback
            )
                
        except Exception as e:
            import traceback
            traceback.print_exc()
            if not self._cancelled:
                self.text_ready.emit(f"<p style='color:red;'>Error: {str(e)}</p>", self.fetch_id)
