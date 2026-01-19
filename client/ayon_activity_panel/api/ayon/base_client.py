import os
import requests
from typing import Dict, Any
from ayon_api import get_server_api_connection


class BaseAyonClient:
    def __init__(self) -> None:
        os.environ.setdefault("AYON_SERVER_URL", "http://localhost:5000")
        os.environ.setdefault("AYON_API_KEY", "cdeaedca95c1f38c8e9d52c8ad9f718e10b9cf6b7bf2c68eac738f5cf037b020")

        # os.environ.setdefault("AYON_SERVER_URL", "http://localhost:5000")
        # os.environ.setdefault("AYON_API_KEY", "c70c93bf3210a1adb354047751cef015e5f59f91975bba38b1a7b1ef50a4217f")

        try:
            self.ayon_connection = get_server_api_connection()
            self.connection_error = None
        except Exception as e:
            self.ayon_connection = None
            self.connection_error = str(e)

    def _execute_graphql(self, query: str, variables: Dict[str, Any]) -> Dict[str, Any]:
        """Execute GraphQL query and return data."""
        result = self.graphql_query(query, variables)
        if result and "data" in result:
            return result["data"]
        return {}

    @staticmethod
    def graphql_query(query: str, variables: Dict[str, Any]) -> Dict[str, Any]:
        try:
            url = os.environ.get("AYON_SERVER_URL", "").rstrip("/") + "/graphql"
            api_key = os.environ.get("AYON_API_KEY", "")

            if not url or not api_key:
                raise Exception("Missing AYON_SERVER_URL or AYON_API_KEY environment variables")

            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            }

            response = requests.post(
                url,
                json={"query": query, "variables": variables},
                headers=headers,
                timeout=30
            )
            response.raise_for_status()
            return response.json()

        except requests.Timeout:
            raise Exception("Request timeout - server may be unavailable")
        except requests.RequestException as e:
            raise Exception(f"Network error: {e}")
        except Exception as e:
            raise Exception(f"GraphQL query failed: {e}")