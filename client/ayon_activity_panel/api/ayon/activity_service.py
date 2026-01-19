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
                    return file_id, (img_data, mime_type)
                return file_id, None
            except Exception:
                return file_id, None

        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
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
                entity_type=entity_type,
                entity_id=entity_id,
                activity_type='comment',
                body=formatted_message,
                file_ids=file_ids or None
            )
            return file_ids
        except Exception as e:
            print(f"Error creating comment: {e}")
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
        for i, fp in enumerate(file_paths):
            try:
                file_id = self.file_service.upload_file(project_name, fp)
                file_ids.append(file_id)
            except Exception as e:
                print(f"    ❌ Upload failed: {e}")
                import traceback
                traceback.print_exc()
        return file_ids

    def process_version_activities(self, project_name: str, version_id: str,
                                   task_id: Optional[str] = None,
                                   path: Optional[str] = None,
                                   status_colors: dict = None,
                                   update_callback=None) -> str:
        """Optimized UX: instant text + smart image loading."""
        if self.ayon_connection is None:
            return "<p>Connection error: Unable to load activities</p>"

        try:
            # Collect entity IDs to fetch activities from
            entity_ids = [version_id]  # Always include version

            # Add task if available
            if task_id and task_id != "N/A":
                entity_ids.append(task_id)

            # Fetch activities using AyonClient API
            from .ayon_client_api import AyonClient
            client = AyonClient()
            response = client.get_activities(
                project_name=project_name,
                entity_ids=entity_ids,
                activity_types=['comment', 'status.change']
            )

            # Extract activities from GraphQL response
            activities = []
            if response and 'project' in response and response['project']:
                edges = response['project'].get('activities', {}).get('edges', [])
                # Deduplicate activities by ID (same activity can appear for both version and task)
                seen_ids = set()
                for edge in edges:
                    if edge.get('node'):
                        activity = edge['node']
                        # Use a combination of fields to create unique ID
                        activity_id = f"{activity.get('activityType')}_{activity.get('createdAt')}_{activity.get('body', '')[:50]}"
                        if activity_id not in seen_ids:
                            seen_ids.add(activity_id)
                            activities.append(activity)
                # Reverse to show newest first
                activities.reverse()
        except Exception as e:
            return f"<p>Error loading activities: {e}</p>"

        try:
            text_html = self._generate_text_html(activities, status_colors)
            if update_callback:
                update_callback(text_html, "text_ready")

            all_files = []
            for activity in activities:
                if activity['activityType'] == 'comment':
                    data = activity.get('activityData', {})
                    # Parse activityData if it's a JSON string
                    if isinstance(data, str):
                        try:
                            import json
                            data = json.loads(data)
                        except:
                            data = {}
                    files = data.get("files", [])
                    all_files.extend(files)

            if all_files and update_callback:
                update_callback(len(all_files), "image_count")
                self._load_images_smart(project_name, all_files, update_callback)

            return text_html
        except Exception as e:
            return f"<p>Error processing activities: {e}</p>"

    def _generate_text_html(self, activities, status_colors=None):
        """Generate instant text-only HTML for immediate display."""
        html_output = "<div style='font-family: Arial, sans-serif; color: #ffffff; background-color: transparent;'>\n"

        for i, activity in enumerate(activities):
            bg_color = "rgba(255,255,255,0.05)" if i % 2 == 0 else "transparent"
            activity_type = activity['activityType']
            body = activity.get('body', '')
            data = activity.get('activityData', {})

            # Parse activityData if it's a JSON string
            if isinstance(data, str):
                try:
                    import json
                    data = json.loads(data)
                except:
                    data = {}

            if activity_type == 'comment':
                import html, re
                # Get author from activity.author.name or activityData.author
                author_obj = activity.get('author', {})
                if isinstance(author_obj, dict):
                    author = html.escape(author_obj.get('name', 'Unknown'))
                else:
                    author = html.escape(data.get('author', 'Unknown'))

                # Get timestamp
                created_at = activity.get('createdAt', '')
                timestamp = self._format_timestamp(created_at)

                # Clean message - remove all markdown-style tags [text](type:id)
                clean_msg = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", body) or "(no message)"
                clean_msg = html.escape(clean_msg.strip()).replace('\n', '<br/>')

                html_output += f"""
                <div style="background-color: {bg_color}; padding: 8px; margin: 2px 0;">
                    🗨️ Comment (by {author}) - <span style="color: #888; font-size: 11px;">{timestamp}</span><br/>
                    &emsp;- {clean_msg}<br/>
                """

                files = data.get("files", [])
                # Filter out annotation files
                filtered_files = [f for f in files if not f['filename'].startswith('annotation-')]
                if filtered_files:
                    html_output += f"&emsp;📎 {len(filtered_files)} attachment(s):<br/>"
                    for file_info in filtered_files:
                        filename = file_info['filename']
                        file_id = file_info['id']
                        html_output += f'''
                        <span style="display: inline-block; width: 200px; margin: 5px; text-align: center; vertical-align: top;">
                            <div id="loading_{file_id}">Loading...</div>
                            <div style="font-size: 11px; color: #aaa; margin-top: 4px;">{filename}</div>
                        </span>
                        '''
                    html_output += '<br/>'

                html_output += "<hr style='border: none; border-top: 1px solid #666;'/>\n</div>"

            elif activity_type == 'status.change':
                import html
                # Get author from activity.author.name or activityData.author
                author_obj = activity.get('author', {})
                if isinstance(author_obj, dict):
                    author = html.escape(author_obj.get('name', 'Unknown'))
                else:
                    author = html.escape(data.get('author', 'Unknown'))

                # Get timestamp
                created_at = activity.get('createdAt', '')
                timestamp = self._format_timestamp(created_at)

                old_status = html.escape(data.get("oldValue", "Unknown"))
                new_status = html.escape(data.get("newValue", "Unknown"))

                old_color = status_colors.get(old_status, '#ffffff') if status_colors else '#ffffff'
                new_color = status_colors.get(new_status, '#ffffff') if status_colors else '#ffffff'

                html_output += f"""
                <div style="background-color: {bg_color}; padding: 8px; margin: 2px 0;">
                    🔄 Status Change (by {author}) - <span style="color: #888; font-size: 11px;">{timestamp}</span><br/>
                    &emsp;changed status from '<i style="color: {old_color}">{old_status}</i>' ➜ '<i style="color: {new_color}">{new_status}</i>'<br/>
                    <hr style='border: none; border-top: 1px solid #666;'/>
                </div>
                """

        html_output += "</div>"

        return html_output

    def _format_timestamp(self, timestamp_str):
        """Format ISO timestamp to readable format in local timezone."""
        if not timestamp_str:
            return "Unknown time"

        try:
            from datetime import datetime
            # Parse ISO format: 2024-01-15T10:30:00Z
            dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            # Convert to local timezone
            dt_local = dt.astimezone()
            # Format as: Jan 15, 2024 10:30 AM
            return dt_local.strftime("%b %d, %Y %I:%M %p")
        except:
            return timestamp_str

    def _load_images_smart(self, project_name, files, update_callback):
        """Smart image loading with progress tracking."""

        def load_and_update():
            results = self._download_file_batch(project_name, files)

            for file_info in files:
                file_id = file_info['id']
                result = results.get(file_id)

                if result and result[0]:
                    img_data, mime_type = result
                    filename = file_info['filename']
                    img_tag = f'<a href="preview:{file_id}:{filename}"><img src="data:{mime_type};base64,{img_data}" width="200" height="100" style="border: 1px solid #666; cursor: pointer; background-color: transparent;" title="Click to preview"/></a>'
                    update_callback((file_id, img_tag, img_data), "image_ready")
                else:
                    error_tag = '<div style="width: 200px; height: 100px; border: 1px solid #ff6666; color: #ff6666; display: flex; align-items: center; justify-content: center;">⚠️ Failed to load</div>'
                    update_callback((file_id, error_tag, None), "image_ready")

        import threading
        threading.Thread(target=load_and_update, daemon=True).start()
