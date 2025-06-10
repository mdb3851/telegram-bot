import json
import os

VIDEO_FILE = "videos.json"
USER_FILE = "users.json"

def load_data(file_path):
    if not os.path.exists(file_path):
        return {}
    with open(file_path, "r") as f:
        return json.load(f)

def save_data(file_path, data):
    with open(file_path, "w") as f:
        json.dump(data, f, indent=2)

def save_video(video_id, file_id):
    data = load_data(VIDEO_FILE)
    data[video_id] = file_id
    save_data(VIDEO_FILE, data)

def get_video(video_id):
    return load_data(VIDEO_FILE).get(video_id)

def save_user(user_id):
    data = load_data(USER_FILE)
    data[str(user_id)] = True
    save_data(USER_FILE, data)

def get_users():
    return list(load_data(USER_FILE).keys())
