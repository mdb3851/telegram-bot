import uuid
from .database import save_video

def generate_video_id():
    return str(uuid.uuid4())

def store_video(file_id):
    video_id = generate_video_id()
    save_video(video_id, file_id)
    return video_id
