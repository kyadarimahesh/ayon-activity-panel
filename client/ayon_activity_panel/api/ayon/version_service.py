from __future__ import annotations

import logging
from typing import Optional, List, Dict, Any
from .base_client import BaseAyonClient

logger = logging.getLogger(__name__)


class VersionService(BaseAyonClient):
    def get_version_thumbnail_to_local(self, project_name: str, version_id: str) -> Optional[str]:
        if self.ayon_connection is None:
            logger.error(f"Connection error: {self.connection_error}")
            return None
        try:
            thumbnail = self.ayon_connection.get_version_thumbnail(project_name, version_id=version_id)
            import tempfile
            with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as temp_thumb:
                temp_thumb.write(thumbnail.content)
                return temp_thumb.name
        except Exception as e:
            logger.error(f"Error getting thumbnail for version {version_id}: {e}")
            return None

    def get_version_thumbnail_data(self, project_name: str, version_id: str) -> Optional[bytes]:
        if self.ayon_connection is None:
            logger.error(f"Connection error: {self.connection_error}")
            return None

        try:
            thumbnail = self.ayon_connection.get_version_thumbnail(project_name, version_id=version_id)
            if thumbnail and hasattr(thumbnail, 'content'):
                return thumbnail.content
            return None
        except Exception as e:
            logger.error(f"Error getting thumbnail data for version {version_id}: {e}")
            return None

    def get_versions_for_product(self, project_name: str, product_id: str) -> List[Dict[str, Any]]:
        try:
            versions = [version['id'] for version in
                        list(self.ayon_connection.get_versions(project_name, product_ids=[product_id]))]
            return versions
        except Exception as e:
            logger.error(f"Error getting versions for project {project_name}: {e}")
            return []

    def get_version_details(self, project_name: str, version_id: str) -> Dict[str, Any]:
        try:
            query = """
            query ($project: String!, $version_id: String!) {
                project(name: $project) {
                    version(id: $version_id) {
                        representations {
                            edges {
                              node {
                                attrib {
                                  path
                                  description
                                  frameEnd
                                  frameStart
                                  handleEnd
                                  handleStart
                                  fps
                                }
                              }
                            }
                          }
                          thumbnailId
                          version
                          productId
                          product {
                            name
                            folder{
                              path
                            }
                          }
                          hasReviewables
                          name
                          status
                        }
                      }
                    }
            """
            result = self.graphql_query(query, {"project": project_name, "version_id": version_id})

            if not result or not result.get("data") or not result.get("data").get("project") or not result.get(
                    "data").get("project").get("version"):
                return {'representations': [], 'meta_data': {}}

            version_data = result["data"]["project"]["version"]

            representations = []
            if version_data.get("representations") and version_data["representations"].get("edges"):
                representations = [
                    node["node"]["attrib"]
                    for node in version_data["representations"]["edges"]
                    if node and node.get("node") and node["node"].get("attrib")
                ]

            meta_data = {
                key: version_data.get(key, "N/A")
                for key in ('hasReviewables', 'productId', 'thumbnailId',
                            'version', 'name', 'status', 'product')
            }

            return {
                'representations': representations,
                'meta_data': meta_data
            }
        except Exception as e:
            logger.error(f"Error getting representations for version {version_id}: {e}")
            return {'representations': [], 'meta_data': {}}

    def update_version_status(self, project_name: str, version_id: str, status: str) -> bool:
        """Update version status."""
        if self.ayon_connection is None:
            logger.error(f"Connection error: {self.connection_error}")
            return False

        try:
            self.ayon_connection.update_version(project_name, version_id, status=status)
            return True
        except Exception as e:
            logger.error(f"Error updating version {version_id} status to {status}: {e}")
            return False

    def update_task_status(self, project_name: str, task_id: str, status: str) -> bool:
        """Update task status."""
        if self.ayon_connection is None:
            logger.error(f"Connection error: {self.connection_error}")
            return False

        try:
            self.ayon_connection.update_task(project_name, task_id, status=status)
            return True
        except Exception as e:
            logger.error(f"Error updating task {task_id} status to {status}: {e}")
            return False

    def get_version_reviewables(self, project_name: str, version_id: str) -> List[Dict[str, Any]]:
        """Get reviewables for a version."""
        if self.ayon_connection is None:
            logger.error(f"Connection error: {self.connection_error}")
            return []

        try:
            response = self.ayon_connection.get(f"/projects/{project_name}/versions/{version_id}/reviewables")
            if response.status_code == 200 and response.data.get('reviewables'):
                return response.data['reviewables']
            return []
        except Exception as e:
            logger.error(f"Error getting reviewables for version {version_id}: {e}")
            return []

    def get_version_statuses(self, project_name: str) -> List[Dict[str, str]]:
        """Get available version statuses for a project."""
        if self.ayon_connection is None:
            logger.error(f"Connection error: {self.connection_error}")
            return []

        if not project_name:
            return []

        try:
            query = """
            query GetVersionStatuses($projectName: String!) {
                project(name: $projectName) {
                    statuses {
                        name
                        color
                        icon
                        scope
                    }
                }
            }
            """
            result = self.graphql_query(query, {"projectName": project_name})

            if result and "data" in result and result["data"].get("project"):
                statuses = result["data"]["project"]["statuses"]
                return [
                    {"value": status["name"], "color": status.get("color"), "icon": status.get("icon")}
                    for status in statuses
                    if "version" in status.get("scope", [])
                ]
            return []
        except Exception as e:
            logger.error(f"Error getting version statuses for project {project_name}: {e}")
            return []

    def get_task_statuses(self, project_name: str) -> List[Dict[str, str]]:
        """Get available task statuses for a project."""
        if self.ayon_connection is None:
            logger.error(f"Connection error: {self.connection_error}")
            return []

        if not project_name:
            return []

        try:
            query = """
            query GetTaskStatuses($projectName: String!) {
                project(name: $projectName) {
                    statuses {
                        name
                        color
                        icon
                        scope
                    }
                }
            }
            """
            result = self.graphql_query(query, {"projectName": project_name})

            if result and "data" in result and result["data"].get("project"):
                statuses = result["data"]["project"]["statuses"]
                return [
                    {"value": status["name"], "color": status.get("color"), "icon": status.get("icon")}
                    for status in statuses
                    if "task" in status.get("scope", [])
                ]
            return []
        except Exception as e:
            logger.error(f"Error getting task statuses for project {project_name}: {e}")
            return []

    def build_version_data_from_id(self, project_name: str, version_id: str) -> Optional[Dict[str, Any]]:
        """Build complete version_data dictionary from version_id.
        
        This centralizes version_data building so integrations only need to pass version_id.
        
        Args:
            project_name: Project name
            version_id: Version ID
            
        Returns:
            Complete version_data dict or None if version not found
        """
        if self.ayon_connection is None:
            logger.error(f"Connection error: {self.connection_error}")
            return None

        try:
            import ayon_api

            version = ayon_api.get_version_by_id(project_name, version_id)
            if not version:
                logger.error(f"Version not found: {version_id}")
                return None

            product_id = version.get("productId")
            task_id = version.get("taskId")
            folder_path = ""
            product_name = "Unknown"
            all_product_versions = []
            versions_list = []
            representations = []

            if product_id:
                product = ayon_api.get_product_by_id(project_name, product_id)
                if product:
                    product_name = product.get("name", "Unknown")
                    folder_id = product.get("folderId")
                    if folder_id:
                        folder = ayon_api.get_folder_by_id(project_name, folder_id)
                        if folder:
                            folder_path = folder.get("path", "")

                    all_product_versions = list(ayon_api.get_versions(
                        project_name,
                        product_ids=[product_id],
                        fields=["id", "version", "status", "author", "taskId"]
                    ))
                    versions_list = [
                        f"v{v['version']:03d}"
                        for v in sorted(all_product_versions, key=lambda x: x['version'], reverse=True)
                    ]

            # Fetch representations
            for rep in ayon_api.get_representations(project_name, version_ids=[version_id]):
                representations.append({
                    'id': rep['id'],
                    'name': rep['name'],
                    'path': rep.get('attrib', {}).get('path', '')
                })

            return {
                "version_id": version_id,
                "project_name": project_name,
                "product_id": product_id,
                "product_name": product_name,
                "task_id": task_id,
                "current_version": f"v{version.get('version', 1):03d}",
                "version_status": version.get("status", "N/A"),
                "author": version.get("author", "N/A"),
                "path": folder_path,
                "versions": versions_list,
                "all_product_versions": all_product_versions,
                "representations": representations,
            }
        except Exception as e:
            logger.error(f"Error building version data for {version_id}: {e}")
            return None
