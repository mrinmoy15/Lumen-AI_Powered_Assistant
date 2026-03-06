"""db/database_utils.py — SQLite thread tracker for LUMEN."""
import sqlite3
from datetime import datetime, timedelta, timezone
from config import DB_PATH

connection = sqlite3.connect(database=str(DB_PATH), check_same_thread=False)


def initialize_thread_tracker():
    cursor = connection.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS thread_tracker (
            thread_id  TEXT PRIMARY KEY,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    connection.commit()


def cleanup_old_threads(days: int = 7):
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    cursor = connection.cursor()
    cursor.execute(
        "SELECT thread_id FROM thread_tracker WHERE created_at < ?", (cutoff,)
    )
    old_threads = [row[0] for row in cursor.fetchall()]
    for tid in old_threads:
        cursor.execute("DELETE FROM checkpoints    WHERE thread_id = ?", (tid,))
        cursor.execute("DELETE FROM writes         WHERE thread_id = ?", (tid,))
        cursor.execute("DELETE FROM thread_tracker WHERE thread_id = ?", (tid,))
    connection.commit()
    print(f"Cleaned up {len(old_threads)} threads older than {days} days")


def delete_thread(thread_id: str):
    """Delete a thread and all its checkpoint data."""
    tid = str(thread_id)
    cursor = connection.cursor()
    cursor.execute("DELETE FROM thread_tracker WHERE thread_id = ?", (tid,))
    cursor.execute("DELETE FROM writes         WHERE thread_id = ?", (tid,))
    cursor.execute("DELETE FROM checkpoints    WHERE thread_id = ?", (tid,))
    connection.commit()
