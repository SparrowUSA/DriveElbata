import io
import time
import random
from googleapiclient.discovery import build


def get_drive():
    from google.oauth2.service_account import Credentials
    import json
    import os

    creds_json = os.environ["GOOGLE_SERVICE_ACCOUNT_JSON"]
    creds = Credentials.from_service_account_info(json.loads(creds_json), scopes=["https://www.googleapis.com/auth/drive"])
    return build("drive", "v3", credentials=creds)


def detect_folder(filename):
    if filename.endswith((".mp4", ".mkv")):
        return "Videos"
    if filename.endswith((".jpg", ".jpeg", ".png")):
        return "Photos"
    return "Documents"


def ensure_folder(drive, folder_name, parent=None):
    query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder'"
    if parent:
        query += f" and '{parent}' in parents"
    results = drive.files().list(q=query, fields="files(id, name)").execute().get("files", [])

    if results:
        return results[0]["id"]

    folder = {"name": folder_name, "mimeType": "application/vnd.google-apps.folder"}
    if parent:
        folder["parents"] = [parent]

    created = drive.files().create(body=folder, fields="id").execute()
    return created["id"]


def upload_to_drive(file_obj, filename, retries=3):
    drive = get_drive()

    root = ensure_folder(drive, "Telegram_Uploads")
    sub = ensure_folder(drive, detect_folder(filename), root)

    media = io.BytesIO(file_obj)

    body = {"name": filename, "parents": [sub]}

    for attempt in range(retries):
        try:
            uploaded = drive.files().create(
                body=body,
                media_body=io.BytesIO(file_obj),
                fields="id"
            ).execute()
            return f"https://drive.google.com/file/d/{uploaded['id']}/view"
        except Exception:
            time.sleep(2 ** attempt + random.random())

    return None
