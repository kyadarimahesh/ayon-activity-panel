"""Review handler for launching OpenRV."""

from ayon_core.lib import Logger

log = Logger.get_logger(__name__)


class ReviewHandler:
    """Handles review submission by launching OpenRV."""

    def __init__(self, parent):
        """Initialize review handler.
        
        Args:
            parent: Parent ActivityPanel widget.
        """
        self.parent = parent

    def launch_review(self):
        """Launch OpenRV with current context."""
        if not self.parent.project_name or not self.parent.current_version_data:
            log.warning("No version data available for review")
            return

        try:
            from ayon_applications import ApplicationManager
            import ayon_api

            # Get context from current version data
            folder_path = self.parent.current_version_data.get("path")
            task_name = self.parent.current_version_data.get("task_name")

            # For DCC mode, extract task name from task_id
            if not task_name:
                task_id = self.parent.current_version_data.get("task_id")
                if task_id:
                    task = ayon_api.get_task_by_id(self.parent.project_name, task_id)
                    if task:
                        task_name = task.get("name")

            if not folder_path:
                log.error("No folder path available for review")
                return

            # Launch OpenRV
            app_manager = ApplicationManager()
            openrv_app = app_manager.find_latest_available_variant_for_group("openrv")

            if not openrv_app:
                log.error("OpenRV not configured. Please configure it in Applications settings.")
                return

            log.info(f"Launching OpenRV: project={self.parent.project_name}, folder={folder_path}, task={task_name}")
            openrv_app.launch(
                project_name=self.parent.project_name,
                folder_path=folder_path,
                task_name=task_name,
                start_last_workfile=True
            )
        except Exception as e:
            log.error(f"Failed to launch OpenRV: {e}", exc_info=True)
