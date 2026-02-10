"""Base client for AYON API connections.

Connection Pool Configuration:
- get_requests_session(): Configures pool for direct GraphQL queries (used by graphql_query method)
- configure_ayon_connection_pool(): Configures pool for ayon_api library calls (used by self.ayon_connection.get/post)

Both are required because the codebase uses two different connection methods:
1. Direct HTTP via requests (GraphQL queries)
2. ayon_api library (REST endpoints like get_version_thumbnail, get_activities)

Without both configurations, urllib3 connection pool warnings occur during concurrent operations.
"""
import os
import requests
from typing import Dict, Any
from ayon_api import get_server_api_connection
from urllib3.util.retry import Retry

# Shared session for connection pooling
_session = None
_ayon_pool_configured = False


def _create_pool_adapter():
    """Create HTTPAdapter with large connection pool."""
    return requests.adapters.HTTPAdapter(
        pool_connections=50,
        pool_maxsize=50,
        max_retries=Retry(
            total=3,
            backoff_factor=0.3,
            status_forcelist=[429, 500, 502, 503, 504]
        ),
        pool_block=False
    )


def get_requests_session():
    """Get or create shared requests session with proper connection pooling.

    Used by: graphql_query() method for direct GraphQL HTTP requests.
    """
    global _session
    if _session is None:
        _session = requests.Session()
        adapter = _create_pool_adapter()
        _session.mount('http://', adapter)
        _session.mount('https://', adapter)
    return _session


def configure_ayon_connection_pool(connection):
    """Configure ayon_api connection pool to prevent exhaustion.

    Used by: self.ayon_connection REST API calls (get_version_thumbnail, get_activities, etc.)
    Configures the internal session of GlobalServerAPI to use larger connection pool.
    """
    global _ayon_pool_configured
    if _ayon_pool_configured or not connection:
        return

    try:
        # GlobalServerAPI uses _session not session
        session = getattr(connection, '_session', None) or getattr(connection, 'session', None)

        if session:
            adapter = _create_pool_adapter()
            session.mount('http://', adapter)
            session.mount('https://', adapter)
            _ayon_pool_configured = True
    except Exception:
        pass


class BaseAyonClient:
    def __init__(self) -> None:
        try:
            self.ayon_connection = get_server_api_connection()
            configure_ayon_connection_pool(self.ayon_connection)
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

            session = get_requests_session()
            response = session.post(
                url,
                json={"query": query, "variables": variables},
                headers=headers,
                timeout=30
            )
            response.raise_for_status()
            result = response.json()
            # Explicitly close connection to return to pool
            response.close()
            return result

        except requests.Timeout:
            raise Exception("Request timeout - server may be unavailable")
        except requests.RequestException as e:
            raise Exception(f"Network error: {e}")
        except Exception as e:
            raise Exception(f"GraphQL query failed: {e}")
