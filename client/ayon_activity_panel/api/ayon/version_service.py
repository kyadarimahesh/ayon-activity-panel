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

        try:
            query = """
            query GetVersionStatuses($projectName: String!) {
                project(name: $projectName) {
                    statuses {
                        name
                        color
                        scope
                    }
                }
            }
            """
            result = self.graphql_query(query, {"projectName": project_name})

            if result and "data" in result and result["data"].get("project"):
                statuses = result["data"]["project"]["statuses"]
                return [
                    {"value": status["name"], "color": status.get("color")}
                    for status in statuses
                    if "version" in status.get("scope", [])
                ]
            return []
        except Exception as e:
            logger.error(f"Error getting version statuses for project {project_name}: {e}")
            return []