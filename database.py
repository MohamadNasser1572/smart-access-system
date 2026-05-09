import os
import sqlite3
from queue import Queue
from threading import Thread

DB_PATH = os.path.join(os.path.dirname(__file__), "system.db")

conn = sqlite3.connect(DB_PATH, check_same_thread=False)
cursor = conn.cursor()

cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        risk TEXT
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
