import os
import sqlite3
from queue import Queue
from threading import Lock, Thread
from typing import List, Tuple

DB_PATH = os.path.join(os.path.dirname(__file__), "system.db")

conn = sqlite3.connect(DB_PATH, check_same_thread=False)
cursor = conn.cursor()
db_lock = Lock()

cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        risk TEXT
    )
    """
)
cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS faces (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        risk_level TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """
)
conn.commit()

log_queue: Queue = Queue()
log_worker_thread: Thread | None = None


def _log_worker() -> None:
    while True:
        item = log_queue.get()
        if item is None:
            break
        name, risk = item
        try:
            with db_lock:
                cursor.execute("INSERT INTO logs (name, risk) VALUES (?, ?)", (name, risk))
                conn.commit()
        except Exception as e:
            print(f"[error] failed to log event: {e}")


def _start_worker() -> None:
    global log_worker_thread
    if log_worker_thread is None or not log_worker_thread.is_alive():
        log_worker_thread = Thread(target=_log_worker, daemon=True)
        log_worker_thread.start()


def log_event(name: str, risk: str) -> None:
    _start_worker()
    log_queue.put((name, risk))


def stop_logging() -> None:
    log_queue.put(None)
    if log_worker_thread:
        log_worker_thread.join(timeout=2)


def add_face(name: str, risk_level: str) -> bool:
    try:
        with db_lock:
            cursor.execute(
                "INSERT INTO faces (name, risk_level) VALUES (?, ?)",
                (name, risk_level),
            )
            conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    except Exception as e:
        print(f"[error] failed to add face: {e}")
        return False


def remove_face(name: str) -> bool:
    try:
        with db_lock:
            cursor.execute("DELETE FROM faces WHERE name = ?", (name,))
            conn.commit()
            return cursor.rowcount > 0
    except Exception as e:
        print(f"[error] failed to remove face: {e}")
        return False


def get_all_faces() -> List[Tuple[str, str]]:
    try:
        with db_lock:
            cursor.execute("SELECT name, risk_level FROM faces ORDER BY name")
            return cursor.fetchall()
    except Exception as e:
        print(f"[error] failed to get faces: {e}")
        return []


def get_face_risk(name: str) -> str | None:
    try:
        with db_lock:
            cursor.execute("SELECT risk_level FROM faces WHERE name = ?", (name,))
            row = cursor.fetchone()
        return row[0] if row else None
    except Exception as e:
        print(f"[error] failed to get face risk: {e}")
        return None
