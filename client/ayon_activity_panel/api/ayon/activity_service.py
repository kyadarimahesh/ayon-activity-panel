from __future__ import annotations

import concurrent.futures
import base64
import mimetypes
from typing import Optional, List, Dict, Tuple
from .base_client import BaseAyonClient
from .file_service import FileService


class ActivityService(BaseAyonClient):
    def __init__(self):
        super().__init__()
        self.file_service = FileService()

    def _download_file_batch(self, project_name: str, file_data: List[Dict]) -> Dict[str, Tuple[str, str]]:
        """Download files in parallel and return base64 data."""
        results = {}

        def download_single_file(file_info):
            file_id, file_name = file_info['id'], file_info['filename']
            try:
                response = self.ayon_connection.get(f"/projects/{project_name}/files/{file_id}")
                if response.status_code == 200:
                    mime_type, _ = mimetypes.guess_type(file_name)
                    img_data = base64.b64encode(response.content).decode('utf-8')
                    # Close response to return connection to pool
                    if hasattr(response, 'close'):
                        response.close()
                    return file_id, (img_data, mime_type)
                if hasattr(response, 'close'):
                    response.close()
                return file_id, None
            except Exception:
                return file_id, None

        # Limit concurrent downloads to avoid pool exhaustion
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            future_to_file = {executor.submit(download_single_file, file_info): file_info['id']
                              for file_info in file_data}

            for future in concurrent.futures.as_completed(future_to_file):
                file_id, result = future.result()
                results[file_id] = result

        return results

    def create_comment_on_version(self, project_name: str, version_id: str, message: str,
                                  user_name: Optional[str] = None,
                                  file_paths: Optional[List[str]] = None,
                                  task_id: Optional[str] = None,
                                  task_name: Optional[str] = None,
                                  path: Optional[str] = None,
                                  version_name: Optional[str] = None) -> Optional[List[str]]:
        try:
            entity_type, entity_id = self._determine_entity(project_name, version_id, task_id, path)
            formatted_message = self._format_message(message, entity_type, version_id, version_name,
                                                     task_id, task_name, user_name)

            file_ids = []
            if file_paths:
                file_ids = self._upload_files(project_name, file_paths)

            self.ayon_connection.create_activity(
                project_name=project_name,
                entity_id=entity_id,
                entity_type=entity_type,
                activity_type='comment',
                body=formatted_message,
                file_ids=file_ids or None
            )
            return file_ids
        except Exception as e:
            print(f"Error creating comment: {e}")
            # Print response body if available
            if hasattr(e, 'response') and hasattr(e.response, 'text'):
                print(f"Response body: {e.response.text}")
            import traceback
            traceback.print_exc()
            return []

    def _determine_entity(self, project_name: str, version_id: str,
                          task_id: Optional[str], path: Optional[str]) -> Tuple[str, str]:
        """Determine entity type and ID with fallback hierarchy."""
        if task_id and task_id != "N/A":
            return "task", task_id

        if path and path != "N/A":
            try:
                folder = self.ayon_connection.get_folder_by_path(project_name, path)
                if folder and folder.get("id"):
                    return "folder", folder["id"]
            except Exception as e:
                print(f"Error getting folder by path: {e}")

        return "version", version_id

    def _format_message(self, message: str, entity_type: str, version_id: str,
                        version_name: Optional[str], task_id: Optional[str],
                        task_name: Optional[str], user_name: Optional[str]) -> str:
        """Format message with version, task, and user tags."""
        tags = []

        # Always tag version
        if version_name and version_id:
            tags.append(f"[{version_name}](version:{version_id})")

        # Tag task if available
        if task_name and task_id and task_id != "N/A":
            tags.append(f"[{task_name}](task:{task_id})")

        # Tag user
        if user_name:
            tags.append(f"[{user_name}](user:{user_name})")

        return f"{' '.join(tags)}\n{message}" if tags else message

    def _upload_files(self, project_name: str, file_paths: List[str]) -> List[str]:
        """Upload files and return their IDs."""
        file_ids = []
        for fp in file_paths:
            try:
                file_id = self.file_service.upload_file(project_name, fp)
                file_ids.append(file_id)
            except Exception as e:
                print(f"    ❌ Upload failed: {e}")
                import traceback
                traceback.print_exc()
        return file_ids

    def update_activity(self, project_name: str, activity_id: str, body: str) -> bool:
        """Update activity body."""
        try:
            self.ayon_connection.update_activity(
                project_name=project_name,
                activity_id=activity_id,
                body=body
            )
            return True
        except Exception as e:
            print(f"Error updating activity: {e}")
            import traceback
            traceback.print_exc()
            return False

    def process_version_activities_native(self, project_name: str, version_id: str,
                                          task_id: Optional[str] = None,
                                          path: Optional[str] = None,
                                          status_colors: dict = None,
                                          version_data: dict = None,
                                          update_callback=None):
        """Process activities and return structured data for native Qt rendering."""

        if self.ayon_connection is None:
            return

        try:
            # Check if DCC mode (no version_id in version_data)
            dcc_mode = version_data and 'version_id' not in version_data

            # Collect entity IDs based on mode
            if dcc_mode:
                # DCC mode: fetch all activities for the task
                entity_ids = [task_id] if task_id and task_id != "N/A" else []
            else:
                # Version mode: fetch activities for version and task
                entity_ids = [version_id]
                if task_id and task_id != "N/A":
                    entity_ids.append(task_id)

            # Fetch activities
            from .ayon_client_api import AyonClient
            client = AyonClient()
            response = client.get_activities(
                project_name=project_name,
                entity_ids=entity_ids,
                activity_types=['comment', 'status.change', 'version.publish'],
                dcc_mode=dcc_mode,
                last=50  # Initial load only
            )

            # Extract all activities (no limit)
            activities = []
            page_info = {}
            if response and 'project' in response and response['project']:
                page_info = response['project'].get('activities', {}).get('pageInfo', {})
                edges = response['project'].get('activities', {}).get('edges', [])
                seen_ids = set()
                for edge in edges:
                    if edge.get('node'):
                        activity = edge['node']
                        activity_id = activity.get('activityId')
                        if activity_id and activity_id not in seen_ids:
                            seen_ids.add(activity_id)
                            activities.append(activity)
                activities.reverse()
        except Exception as e:
            print(f"Error loading activities: {e}")
            return

        # Send activities data with pagination info
        activities_data = {
            'activities': activities,
            'product_name': version_data.get('product_name', 'Unknown') if version_data else 'Unknown',
            'current_version': version_data.get('current_version', 'v000') if version_data else 'v000',
            'status_colors': status_colors or {},
            'page_info': page_info
        }

        if update_callback:
            update_callback(activities_data, "activities_ready")

        # Load images asynchronously
        for idx, activity in enumerate(activities):
            if activity['activityType'] == 'comment':
                data = activity.get('activityData', {})
                if isinstance(data, str):
                    try:
                        import json
                        data = json.loads(data)
                    except:
                        data = {}
                files = data.get("files", [])
                if files and update_callback:
                    self._load_images_for_activity(project_name, idx, files, update_callback)

    def _load_images_for_activity(self, project_name, activity_index, files, update_callback):
        """Load images for specific activity."""

        def load_and_update():
            results = self._download_file_batch(project_name, files)
            for file_info in files:
                file_id = file_info['id']
                filename = file_info.get('filename', 'unknown')
                result = results.get(file_id)
                if result and result[0]:
                    img_data, _ = result
                    update_callback((activity_index, file_id, img_data, filename), "image_ready")

        import threading
        threading.Thread(target=load_and_update, daemon=True).start()
