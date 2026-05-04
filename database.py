import os
import sqlite3

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


def log_event(name: str, risk: str) -> None:
    cursor.execute("INSERT INTO logs (name, risk) VALUES (?, ?)", (name, risk))
    conn.commit()
