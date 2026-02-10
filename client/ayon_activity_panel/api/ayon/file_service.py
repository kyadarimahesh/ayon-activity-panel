import os

import tempfile
from typing import Optional
from pathlib import Path
import ayon_api


class FileService:
    @staticmethod
    def upload_file(project_name: str, file_path: str, activity_id: str = None) -> Optional[str]:
        import mimetypes
        from .base_client import get_requests_session

        try:
            safe_path = Path(file_path).resolve()
            if not safe_path.exists():
                raise FileNotFoundError(f"File not found: {file_path}")
        except (OSError, ValueError) as e:
            print(f"Invalid file path: {e}")
            return None

        mime_type, _ = mimetypes.guess_type(str(safe_path))
        file_name = safe_path.name

        headers = {
            "Content-Type": mime_type or "application/octet-stream",
            "X-File-Name": file_name,
            "Authorization": f"Bearer {os.environ['AYON_API_KEY']}"
        }

        if activity_id:
            headers["X-Activity-Id"] = activity_id

        try:
            session = get_requests_session()
            with open(safe_path, 'rb') as f:
                response = session.post(
                    f"{os.environ['AYON_SERVER_URL']}/api/projects/{project_name}/files",
                    data=f.read(),
                    headers=headers,
                    timeout=30
                )
        except (FileNotFoundError, PermissionError) as e:
            print(f"Error uploading file: {e}")
            return None

        if response.status_code == 201:
            return response.json()["id"]
        return None

    @staticmethod
    def download_file(project_name: str, file_id: str, filename: str = None) -> Optional[str]:
        """Download file and return temporary path."""
        try:
            ayon_con = ayon_api.get_server_api_connection()
            endpoint = f"/projects/{project_name}/files/{file_id}"
            response = ayon_con.get(endpoint)

            if response.status_code != 200:
                print(f"Download failed ({response.status_code}): {response.text}")
                return None

            if not filename:
                filename = file_id

            with tempfile.NamedTemporaryFile(mode='wb', suffix=f"_{filename}", delete=False) as temp_file:
                temp_file.write(response.content)
                return temp_file.name

        except Exception as e:
            print(f"Error downloading file: {e}")
            return None


if __name__ == "__main__":
    # Get reviewables
    ayon_con = ayon_api.get_server_api_connection()
    response = ayon_con.get("/projects/new_project1/versions/637a1ffca72111f0a81402a0afb0ef10/reviewables")
    if response.status_code == 200 and response.data.get('reviewables'):
        reviewables = response.data['reviewables']
        for reviewable in reviewables:
            file_id = reviewable['fileId']
            filename = reviewable.get('filename', file_id)
            print(file_id, filename)

        print(f"Testing download for file: {filename}")
        result = FileService.download_file("new_project1", file_id, filename)
        print(result)
        if result:
            print(f"Download successful: {result}")
            os.startfile(result)
        else:
            print("Download failed")
    else:
        print("No reviewables found")
