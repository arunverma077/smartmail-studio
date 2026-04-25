# db.py — JSON-based database for SmartMail Studio
import os
import json
import time
import hashlib

BASE_DIR = "data"
USERS_DIR = os.path.join(BASE_DIR, "users")
SESSIONS_FILE = os.path.join(BASE_DIR, "sessions.json")


# -----------------------------------------------------
# INITIAL DB SETUP
# -----------------------------------------------------
def init_json_db():
    os.makedirs(USERS_DIR, exist_ok=True)

    if not os.path.exists(SESSIONS_FILE):
        with open(SESSIONS_FILE, "w") as f:
            json.dump({}, f, indent=2)


# -----------------------------------------------------
# PASSWORD HASHING
# -----------------------------------------------------
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


# -----------------------------------------------------
# USER CREATION & AUTH
# -----------------------------------------------------
def create_user(username: str, password: str) -> bool:
    user_dir = os.path.join(USERS_DIR, username)

    if os.path.exists(user_dir):
        return False  # user exists

    os.makedirs(user_dir)

    user_data = {
        "username": username,
        "password_hash": hash_password(password),
        "created_at": int(time.time())
    }

    with open(os.path.join(user_dir, "user.json"), "w") as f:
        json.dump(user_data, f, indent=2)

    # Empty history file
    with open(os.path.join(user_dir, "history.json"), "w") as f:
        json.dump([], f, indent=2)

    return True


def verify_user(username: str, password: str) -> bool:
    user_dir = os.path.join(USERS_DIR, username)

    if not os.path.exists(user_dir):
        return False

    with open(os.path.join(user_dir, "user.json")) as f:
        user_data = json.load(f)

    return user_data["password_hash"] == hash_password(password)


# -----------------------------------------------------
# EMAIL HISTORY
# -----------------------------------------------------
def save_email_to_history(username: str, record: dict):
    hist_file = os.path.join(USERS_DIR, username, "history.json")

    # Load old history
    if os.path.exists(hist_file):
        with open(hist_file) as f:
            history = json.load(f)
    else:
        history = []

    history.insert(0, record)  # newest first

    with open(hist_file, "w") as f:
        json.dump(history, f, indent=2)


def get_user_history(username: str):
    hist_file = os.path.join(USERS_DIR, username, "history.json")

    if not os.path.exists(hist_file):
        return []

    with open(hist_file) as f:
        return json.load(f)


# -----------------------------------------------------
# SESSIONS
# -----------------------------------------------------
def save_session(username: str):
    if not os.path.exists(SESSIONS_FILE):
        with open(SESSIONS_FILE, "w") as f:
            json.dump({}, f)

    with open(SESSIONS_FILE) as f:
        sessions = json.load(f)

    sessions[username] = {
        "username": username,
        "login_time": int(time.time()),
        "expires_at": int(time.time()) + 12 * 3600
    }

    with open(SESSIONS_FILE, "w") as f:
        json.dump(sessions, f, indent=2)


def load_session(username=None):
    if not os.path.exists(SESSIONS_FILE):
        return {} if username in ("*", None) else None

    with open(SESSIONS_FILE) as f:
        sessions = json.load(f)

    if username == "*" or username is None:
        return sessions

    return sessions.get(username)


def clear_session(username: str):
    if not os.path.exists(SESSIONS_FILE):
        return

    with open(SESSIONS_FILE) as f:
        sessions = json.load(f)

    if username in sessions:
        del sessions[username]

    with open(SESSIONS_FILE, "w") as f:
        json.dump(sessions, f, indent=2)
