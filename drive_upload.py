import io
import time
import random
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload


def get_drive():
    from google.oauth2.service_account import Credentials
    import json
    import os

    creds_json = os.environ["GOOGLE_SERVICE_ACCOUNT_JSON"]
    creds = Credentials.from_service_account_info(json.loads(creds_json), scopes=["https://www.googleapis.com/auth/drive"])
    return build("drive", "v3", credentials=creds)



def detect_folder(filename):
    if filename.endswith(".mp4"):
        return "Videos"
    if filename.endswith(".jpg") or filename.endswith(".png"):
        return "Photos"
    return "Documents"



def ensure_folder(drive, folder_name, parent=None):
    query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder'"
    results = drive.files().list(q=query).execute().get("files", [])

    if results:
        return results[0]["id"]

    file = {
        "name": folder_name,
        "mimeType": "application/vnd.google-apps.folder",
    }

    if parent:
        file["parents"] = [parent]

    folder = drive.files().create(body=file).execute()
    return folder["id"]



def upload_to_drive(file_obj, filename, retries=3):
    drive = get_drive()

    parent = ensure_folder(drive, detect_folder(filename))

    media = MediaIoBaseUpload(io.BytesIO(file_obj), mimetype="application/octet-stream")

    body = {"name": filename, "parents": [parent]}

    for attempt in range(retries):

        try:
            uploaded = drive.files().create(body=body, media_body=media, fields="id").execute()
            return f"https://drive.google.com/file/d/{uploaded['id']}/view"

        except Exception:
            time.sleep(2 ** attempt + random.random())

    return None
