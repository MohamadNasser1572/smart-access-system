import sqlite3
from typing import List, Tuple

from fastapi import FastAPI
from database import DB_PATH

app = FastAPI(title="Smart Access System API")


@app.get("/logs")
def get_logs() -> List[Tuple[int, str, str]]:
    conn = sqlite3.connect(DB_PATH)
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
    cursor.execute("SELECT * FROM logs")
    rows = cursor.fetchall()
    conn.close()
    return rows
