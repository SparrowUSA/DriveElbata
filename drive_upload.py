from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import os
import json
import base64
from io import BytesIO


def get_drive_service():
    encoded_json = os.environ["GOOGLE_SERVICE_ACCOUNT_JSON"]
    decoded_json = base64.b64decode(encoded_json)
    info = json.loads(decoded_json)

    credentials = service_account.Credentials.from_service_account_info(
        info,
        scopes=["https://www.googleapis.com/auth/drive"]
    )

    service = build("drive", "v3", credentials=credentials)
    return service


def upload_file_bytes(file_name: str, file_bytes: bytes, folder_id: str = None):
    drive = get_drive_service()

    file_stream = BytesIO(file_bytes)

    file_metadata = {
        "name": file_name
    }

    if folder_id:
        file_metadata["parents"] = [folder_id]

    media = MediaIoBaseUpload(file_stream, mimetype="application/octet-stream")

    uploaded = drive.files().create(
        body=file_metadata,
        media_body=media,
        fields="id, webViewLink"
    ).execute()

    return uploaded
