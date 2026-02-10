"""Comment handler with RV annotation export support."""
from __future__ import annotations

import os
import tempfile

from ayon_core.lib import Logger
from ayon_core.tools.utils.dialogs import show_message_dialog
from ayon_core.tools.utils.overlay_messages import MessageOverlayObject

from ..api import AyonClient

log = Logger.get_logger(__name__)


class RVAnnotationExporter:
    """Handles RV annotation extraction and export."""

    @staticmethod
    def get_annotation_summary() -> dict:
        """Get summary of annotations in current RV session."""
        try:
            import rv.commands as rv_commands
            from pymu import MuSymbol

            marked_frames = rv_commands.markedFrames()
            if not marked_frames:
                mark_frames = MuSymbol('rvui.markAnnotatedFrames')
                mark_frames()
                marked_frames = rv_commands.markedFrames()

            text_annotations = RVAnnotationExporter._extract_text_annotations(marked_frames, rv_commands)

            return {
                'has_annotations': bool(marked_frames),
                'frame_count': len(marked_frames),
                'text_annotations': text_annotations
            }
        except Exception as e:
            log.error(f"Error getting annotation summary: {e}")
            return {'has_annotations': False}

    @staticmethod
    def _extract_text_annotations(marked_frames: list[int], rv_commands) -> str:
        """Extract text from marked frames."""
        if not marked_frames:
            return ""

        annotations = []
        frame_offset = rv_commands.frame() - 1

        for frame in marked_frames:
            texts = RVAnnotationExporter._extract_frame_text(frame, rv_commands)
            for text in texts:
                annotations.append(f"Frame {frame + frame_offset}: {text}")

        return "\n".join(annotations)

    @staticmethod
    def _extract_frame_text(frame: int, rv_commands) -> list[str]:
        """Extract text from specific frame."""
        try:
            prop_order = f"#RVPaint.frame:{frame}.order"
            if not rv_commands.propertyExists(prop_order):
                return []

            texts = []
            items = rv_commands.getStringProperty(prop_order, 0, 2147483647)

            for item in items:
                if item.startswith("text"):
                    text_prop = f"#RVPaint.{item}.text"
                    if rv_commands.propertyExists(text_prop):
                        text = rv_commands.getStringProperty(text_prop, 0, 2147483647)
                        if text and text[0].strip():
                            texts.append(text[0].strip())

            return texts
        except Exception as e:
            log.error(f"Error extracting text from frame {frame}: {e}")
            return []

    @staticmethod
    def export_annotations() -> list[str]:
        """Export annotation images to temp directory."""
        try:
            import time
            from pymu import MuSymbol
            import rv.commands as rv_commands

            marked_frames = rv_commands.markedFrames()
            if not marked_frames:
                mark_frames = MuSymbol('rvui.markAnnotatedFrames')
                mark_frames()
                marked_frames = rv_commands.markedFrames()

            if not marked_frames:
                log.warning("No marked frames to export")
                return []

            temp_dir = tempfile.mkdtemp(prefix="ayon_annotations_")
            export_pattern = os.path.join(temp_dir, "annotated.####.jpeg")

            exportframes = MuSymbol("export_utils.exportMarkedFrames")
            exportframes(export_pattern)

            expected_files = len(marked_frames)
            max_wait = 20
            wait_interval = 0.5
            elapsed = 0
            exported_files = []

            while elapsed < max_wait:
                time.sleep(wait_interval)
                elapsed += wait_interval

                if os.path.exists(temp_dir):
                    files = list(os.listdir(temp_dir))
                    jpeg_files = [f for f in files if f.startswith("annotated") and f.endswith(".jpeg")]

                    if len(jpeg_files) >= expected_files:
                        exported_files = [os.path.join(temp_dir, f) for f in sorted(jpeg_files)]
                        break

            if not exported_files:
                log.warning(
                    f"Expected {expected_files} files, found {len(jpeg_files) if 'jpeg_files' in locals() else 0}")

            return exported_files
        except Exception as e:
            log.error(f"Error exporting annotations: {e}")
            import traceback
            traceback.print_exc()
            return []


class CommentManager:
    """Handles comment creation with RV annotation support."""

    def __init__(self, parent_widget):
        self.parent = parent_widget
        self.ayon_client = AyonClient()

    def create_comment(self, message, version_data, activity_service, project_name, refresh_callback=None,
                       screenshot_paths=None, on_success=None):
        """Create comment with RV annotations if available.
        
        Args:
            message (str): Comment message.
            version_data (dict): Version data.
            activity_service: Activity service instance.
            project_name (str): Project name.
            refresh_callback (callable): Callback to refresh UI after comment.
            screenshot_paths (list): List of screenshot file paths to attach.
            on_success (callable): Callback for cleanup after successful comment.

        Returns:
            bool: True if comment created successfully.
        """
        if not message:
            show_message_dialog(
                "Warning",
                "Please enter a comment message.",
                level="warning",
                parent=self.parent
            )
            return False

        version_id = version_data.get('version_id')
        version_name = version_data.get('current_version')
        task_id = version_data.get('task_id')
        task_name = version_data.get('task_name')
        path = version_data.get('path')
        user_name = version_data.get('author')

        # Fetch version info if version_name or task_id is missing
        if not version_name or not task_id or task_id == "N/A" or task_id is None:
            try:
                import ayon_api
                version = ayon_api.get_version_by_id(project_name, version_id)
                if version:
                    if not version_name:
                        version_name = version.get('name')

                    # Try to get task_id from version
                    if not task_id or task_id == "N/A" or task_id is None:
                        task_id = version.get('taskId')
            except Exception as e:
                log.debug(f"Could not fetch version info: {e}")

        # Fetch task_name if missing but task_id exists
        if task_id and task_id != "N/A" and task_id is not None and not task_name:
            try:
                import ayon_api
                task = ayon_api.get_task_by_id(project_name, task_id)
                task_name = task.get('name') if task else None
            except Exception as e:
                log.debug(f"Could not fetch task name: {e}")

        # Use AYON's overlay message system
        if not hasattr(self.parent, '_overlay_object'):
            self.parent._overlay_object = MessageOverlayObject(self.parent)

        overlay = self.parent._overlay_object
        overlay.add_message("Preparing comment...")

        annotation_paths = screenshot_paths[:] if screenshot_paths else []

        # Check if RV is available for annotation export
        try:
            import rv.commands
            rv_available = True
        except ImportError:
            rv_available = False

        if rv_available:
            try:
                overlay.add_message("Checking for annotations...")
                ann_summary = RVAnnotationExporter.get_annotation_summary()
                log.info(f">>> DEBUG: Annotation summary: {ann_summary}")

                if ann_summary.get('has_annotations'):
                    text_annotations = ann_summary.get('text_annotations', '')
                    if text_annotations:
                        message += f"\n\n--- RV Annotations ---\n{text_annotations}"

                    overlay.add_message("Exporting annotations...")

                    annotation_paths = RVAnnotationExporter.export_annotations()

                    if annotation_paths:
                        overlay.add_message(f"Found {len(annotation_paths)} annotation(s)...")
                    else:
                        log.warning("No annotation images exported")
                else:
                    log.info("No annotations found in RV session")

            except Exception as e:
                log.error(f"Error extracting annotations: {e}", exc_info=True)

        overlay.add_message("Uploading comment...")

        try:
            result = activity_service.create_comment_on_version(
                project_name,
                version_id,
                message,
                user_name=user_name,
                file_paths=annotation_paths,
                task_id=task_id,
                task_name=task_name,
                path=path,
                version_name=version_name
            )

            if result is not None:
                overlay.add_message("✓ Comment created successfully!", message_type="success")

                if on_success:
                    on_success()
                if refresh_callback:
                    refresh_callback()
                return True
            else:
                overlay.add_message("Failed to create comment", message_type="error")
                return False

        except Exception as e:
            log.error(f"Failed to create comment: {e}", exc_info=True)
            overlay.add_message(f"Failed to create comment: {str(e)}", message_type="error")
            return False
