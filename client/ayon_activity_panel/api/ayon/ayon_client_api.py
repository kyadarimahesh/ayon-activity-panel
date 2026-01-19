from typing import Optional, List, Dict, Any

from .version_service import VersionService
from .activity_service import ActivityService

from .file_service import FileService


class AyonClient:
    def __init__(self) -> None:

        self.version_service = VersionService()
        self.activity_service = ActivityService()

        self.file_service = FileService()

    # Version operations
    def get_version_thumbnail_to_local(self, project_name: str, version_id: str) -> Optional[str]:
        return self.version_service.get_version_thumbnail_to_local(project_name, version_id)

    def get_version_thumbnail_data(self, project_name: str, version_id: str) -> Optional[bytes]:
        return self.version_service.get_version_thumbnail_data(project_name, version_id)

    def get_versions_for_product(self, project_name: str, product_id: str) -> List[Dict[str, Any]]:
        return self.version_service.get_versions_for_product(project_name, product_id)

    def get_version_details(self, project_name: str, version_id: str) -> Dict[str, Any]:
        return self.version_service.get_version_details(project_name, version_id)

    # Activity operations
    def create_comment_on_version(self, project_name: str, version_id: str, message: str,
                                  user_name: Optional[str] = None,
                                  file_paths: Optional[List[str]] = None,
                                  task_id: Optional[str] = None,
                                  task_name: Optional[str] = None,
                                  path: Optional[str] = None,
                                  version_name: Optional[str] = None) -> Optional[List[str]]:
        return self.activity_service.create_comment_on_version(project_name, version_id, message, user_name, file_paths,
                                                               task_id, task_name, path, version_name)

    def process_version_activities(self, project_name: str, version_id: str,
                                   task_id: Optional[str] = None,
                                   path: Optional[str] = None,
                                   status_colors: dict = None,
                                   update_callback=None) -> str:
        return self.activity_service.process_version_activities(project_name, version_id, task_id, path,
                                                                status_colors, update_callback)

    # Activity operations (GraphQL)
    def get_activities(self, project_name: str, entity_ids: List[str],
                       reference_types: List[str] = None,
                       activity_types: List[str] = None,
                       last: int = 100, before: str = None) -> Dict:
        """Get activity feed/comments (latest activities)"""
        query = """
        query GetActivities(
          $projectName: String!
          $entityIds: [String!]!
          $before: String
          $last: Int
          $referenceTypes: [String!]
          $activityTypes: [String!]
        ) {
          project(name: $projectName) {
            name
            activities(
              entityIds: $entityIds
              before: $before
              last: $last
              referenceTypes: $referenceTypes
              activityTypes: $activityTypes
            ) {
              pageInfo {
                hasPreviousPage
                hasNextPage
                startCursor
                endCursor
              }
              edges {
                cursor
                node {
                  activityType
                  activityData
                  createdAt
                  updatedAt
                  entityId
                  entityType
                  projectName
                  author {
                    name
                  }
                  referenceType
                  body
                }
              }
            }
          }
        }
        """
        result = self.graphql_query(query, {
            'projectName': project_name,
            'entityIds': entity_ids,
            'referenceTypes': reference_types or ['origin', 'mention', 'relation'],
            'activityTypes': activity_types,
            'last': last,
            'before': before
        })
        return result.get('data', {}) if result else {}

    # File operations
    @staticmethod
    def upload_file(project_name: str, file_path: str, activity_id: str = None) -> Optional[str]:
        return FileService.upload_file(project_name, file_path, activity_id)

    # Status operations
    def get_version_statuses(self, project_name: str) -> List[Dict[str, str]]:
        """Get available version statuses for a project with colors."""
        query = """
        query GetVersionStatuses($projectName: String!) {
            project(name: $projectName) {
                statuses {
                    name
                    color
                    icon
                    shortName
                    state
                    scope
                }
            }
        }
        """
        variables = {"projectName": project_name}
        result = self.graphql_query(query, variables)

        if result and "data" in result and result["data"]["project"]:
            statuses = result["data"]["project"]["statuses"]

            version_statuses = [
                {"value": status["name"], "color": status["color"]}
                for status in statuses
                if "version" in status["scope"]
            ]

            return [{"value": "All"}] + version_statuses

        return [{"value": "All"}]

    # Task type operations
    def get_task_types(self, project_name: str) -> List[Dict[str, str]]:
        """Get available task types for a project with colors and icons."""
        query = """
        query GetTaskTypes($projectName: String!) {
            project(name: $projectName) {
                taskTypes {
                    icon
                    name
                    shortName
                    color
                }
            }
        }
        """
        variables = {"projectName": project_name}
        result = self.graphql_query(query, variables)

        if result and "data" in result and result["data"]["project"]:
            task_types = result["data"]["project"]["taskTypes"]

            task_type_items = [
                {"value": task_type["name"], "color": task_type["color"]}
                for task_type in task_types
            ]

            return [{"value": "All"}] + task_type_items

        return [{"value": "All"}]

    # Version status update
    def update_version_status(self, project_name: str, version_id: str, status: str) -> bool:
        """Update version status."""
        return self.version_service.update_version_status(project_name, version_id, status)

    # GraphQL operations
    @staticmethod
    def graphql_query(query: str, variables: Dict[str, Any]) -> Dict[str, Any]:
        from .base_client import BaseAyonClient
        return BaseAyonClient.graphql_query(query, variables)
