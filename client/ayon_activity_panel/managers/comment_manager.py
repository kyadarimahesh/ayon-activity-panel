"""Comment handler with RV annotation export support."""
import os
import tempfile
import logging
from typing import List

from qtpy.QtWidgets import QProgressDialog, QMessageBox, QApplication
from qtpy.QtCore import Qt, QThread
from ..api import AyonClient

log = logging.getLogger(__name__)


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
            LOG.error(f"Error getting annotation summary: {e}")
            return {'has_annotations': False}

    @staticmethod
    def _extract_text_annotations(marked_frames: List[int], rv_commands) -> str:
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
    def _extract_frame_text(frame: int, rv_commands) -> List[str]:
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
            LOG.error(f"Error extracting text from frame {frame}: {e}")
            return []

    @staticmethod
    def export_annotations() -> List[str]:
        """Export annotation images to temp directory."""
        try:
            import time
            from pymu import MuSymbol

            temp_dir = tempfile.mkdtemp(prefix="ayon_annotations_")
            pattern = os.path.join(temp_dir, "annotated.####.jpeg")

            export_frames = MuSymbol("export_utils.exportMarkedFrames")
            export_frames(pattern)

            # Wait for rvio to finish writing files (matches review_browser)
            max_wait = 20  # seconds
            wait_interval = 0.5  # seconds
            elapsed = 0
            exported_files = []

            while elapsed < max_wait:
                time.sleep(wait_interval)
                elapsed += wait_interval

                if os.path.exists(temp_dir):
                    files = [f for f in os.listdir(temp_dir)
                             if f.startswith("annotated") and f.endswith(".jpeg")]
                    if files:
                        exported_files = [os.path.join(temp_dir, f) for f in files]
                        break

            if not exported_files:
                print(f"  - No files found after {elapsed:.1f}s")
                if os.path.exists(temp_dir):
                    print(f"  - Directory contents: {os.listdir(temp_dir)}")

            return exported_files
        except Exception as e:
            LOG.error(f"Error exporting annotations: {e}")
            import traceback
            traceback.print_exc()
            return []


class CommentHandler:
    """Handles comment creation with RV annotation support."""

    def __init__(self, parent_widget):
        self.parent = parent_widget
        self.ayon_client = AyonClient()

    def create_comment(self, message, version_data, activity_service, project_name, refresh_callback=None):
        """Create comment with RV annotations if available.
        
        Args:
            message (str): Comment message.
            version_data (dict): Version data.
            activity_service: Activity service instance.
            project_name (str): Project name.
            refresh_callback (callable): Callback to refresh UI.
            
        Returns:
            bool: True if comment created successfully.
        """

        if not message:
            QMessageBox.warning(self.parent, "Warning", "Please enter a comment message.")
            return False

        version_id = version_data.get('version_id')
        version_name = version_data.get('current_version')
        task_id = version_data.get('task_id')
        task_name = version_data.get('task_name')
        path = version_data.get('path')
        user_name = version_data.get('author')

        if not version_name:
            import ayon_api
            version = ayon_api.get_version_by_id(project_name, version_id)
            version_name = version.get('name') if version else None

        progress = QProgressDialog("Preparing comment...", None, 0, 0, self.parent)
        progress.setWindowModality(Qt.WindowModal)
        progress.show()
        QApplication.processEvents()
        QThread.msleep(300)

        annotation_paths = []

        # Check if RV integration is active
        if hasattr(self.parent, 'rv_integration') and self.parent.rv_integration:
            try:
                progress.setLabelText("Checking for annotations...")
                QApplication.processEvents()

                ann_summary = RVAnnotationExporter.get_annotation_summary()

                if ann_summary.get('has_annotations'):
                    text_annotations = ann_summary.get('text_annotations', '')
                    if text_annotations:
                        message += f"\n\n--- RV Annotations ---\n{text_annotations}"

                    progress.setLabelText("Exporting annotations...")
                    QApplication.processEvents()
                    QThread.msleep(300)

                    annotation_paths = RVAnnotationExporter.export_annotations()

                    if annotation_paths:
                        progress.setLabelText(f"Found {len(annotation_paths)} annotation(s)...")
                        QApplication.processEvents()
                    else:
                        log.warning("No annotation images exported")
                else:
                    log.info("No annotations found in RV session")

            except Exception as e:
                log.warning(f"Error extracting annotations: {e}")
                import traceback
                traceback.print_exc()
        else:
            if hasattr(self.parent, 'rv_integration'):
                log.debug(f"rv_integration value: {self.parent.rv_integration}")

        progress.setLabelText("Uploading comment...")
        QApplication.processEvents()
        QThread.msleep(200)

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

            progress.close()

            if result is not None:
                QMessageBox.information(self.parent, "Success", "✓ Comment created successfully!")
                if refresh_callback:
                    refresh_callback()
                return True
            else:
                QMessageBox.warning(self.parent, "Error", "Failed to create comment")
                return False

        except Exception as e:
            import traceback
            traceback.print_exc()
            progress.close()
            QMessageBox.critical(self.parent, "Error", f"Failed to create comment: {str(e)}")
            return False
