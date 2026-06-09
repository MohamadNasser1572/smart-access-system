import os
import sqlite3
from queue import Queue
from threading import Lock, Thread
from typing import List, Optional, Tuple

DB_PATH = os.path.join(os.path.dirname(__file__), "system.db")

conn = sqlite3.connect(DB_PATH, check_same_thread=False)
cursor = conn.cursor()
db_lock = Lock()

cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        risk TEXT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """
)
# Bug 18 fix: add timestamp column if it doesn't exist yet (for existing DBs).
try:
    cursor.execute("ALTER TABLE logs ADD COLUMN timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
    conn.commit()
except sqlite3.OperationalError:
    pass  # column already exists

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

# Bug 17 fix: cap the queue so a fast recognition loop can't grow it unboundedly.
log_queue: Queue = Queue(maxsize=500)
# Bug 16 fix: use Optional[Thread] instead of Thread | None (compatible with Python 3.9).
log_worker_thread: Optional[Thread] = None


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
    try:
        log_queue.put_nowait((name, risk))
    except Exception:
        pass  # drop silently if queue is full rather than blocking the camera loop


def stop_logging() -> None:
    # Bug 19 fix: drain pending items before sending the sentinel so a restarted
    # worker doesn't immediately hit None and exit before processing new events.
    try:
        while not log_queue.empty():
            log_queue.get_nowait()
    except Exception:
        pass
    log_queue.put(None)
    if log_worker_thread:
        log_worker_thread.join(timeout=2)


def add_face(name: str, risk_level: str) -> bool:
    try:
        with db_lock:
            cursor.execute("SELECT 1 FROM faces WHERE name = ?", (name,))
            exists = cursor.fetchone() is not None

            if exists:
                cursor.execute(
                    "UPDATE faces SET risk_level = ? WHERE name = ?",
                    (risk_level, name),
                )
            else:
                cursor.execute(
                    "INSERT INTO faces (name, risk_level) VALUES (?, ?)",
                    (name, risk_level),
                )
            conn.commit()
        from risk_engine import invalidate_risk_cache
        invalidate_risk_cache(name)
        return True
    except Exception as e:
        print(f"[error] failed to add face: {e}")
        return False


def update_face_risk(name: str, risk_level: str) -> bool:
    try:
        with db_lock:
            cursor.execute("UPDATE faces SET risk_level = ? WHERE name = ?", (risk_level, name))
            conn.commit()
            updated = cursor.rowcount > 0
        if updated:
            from risk_engine import invalidate_risk_cache
            invalidate_risk_cache(name)
        return updated
    except Exception as e:
        print(f"[error] failed to update face risk: {e}")
        return False


def remove_face(name: str) -> bool:
    try:
        with db_lock:
            cursor.execute("DELETE FROM faces WHERE name = ?", (name,))
            conn.commit()
            removed = cursor.rowcount > 0
        if removed:
            from risk_engine import invalidate_risk_cache
            invalidate_risk_cache(name)
        return removed
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


def get_face_risk(name: str) -> Optional[str]:
    try:
        with db_lock:
            cursor.execute("SELECT risk_level FROM faces WHERE name = ?", (name,))
            row = cursor.fetchone()
        return row[0] if row else None
    except Exception as e:
        print(f"[error] failed to get face risk: {e}")
        return None


def get_logs(limit: int = 200) -> List[dict]:
    # Bug 3 fix: use the shared connection with lock; return recent rows only.
    try:
        with db_lock:
            cursor.execute(
                "SELECT id, name, risk, timestamp FROM logs ORDER BY id DESC LIMIT ?",
                (limit,),
            )
            rows = cursor.fetchall()
        return [{"id": r[0], "name": r[1], "risk": r[2], "timestamp": r[3]} for r in rows]
    except Exception as e:
        print(f"[error] failed to get logs: {e}")
        return []
