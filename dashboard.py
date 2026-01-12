from fastapi import FastAPI
from queue_manager import UploadQueue

app = FastAPI()
queue_ref: UploadQueue = None


def bind_queue(q):
    global queue_ref
    queue_ref = q


@app.get("/")
def home():
    return {"message": "Telegram to Google Drive Bot Dashboard"}


@app.get("/stats")
def stats():
    return {
        "pending": queue_ref.pending(),
        "uploaded": queue_ref.total_uploaded,
        "failed": queue_ref.total_failed,
        "paused": queue_ref.paused
    }
