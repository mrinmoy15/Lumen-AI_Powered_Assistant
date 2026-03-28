"""db/database_utils.py — PostgreSQL thread tracker for LUMEN."""
import psycopg
from datetime import datetime, timedelta, timezone
from config import DATABASE_URL


def _get_conn():
    return psycopg.connect(DATABASE_URL)


def initialize_thread_tracker():
    with _get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS thread_tracker (
                    thread_id  TEXT PRIMARY KEY,
                    created_at TIMESTAMPTZ DEFAULT NOW()
                )
            """)
        conn.commit()


def cleanup_old_threads(days: int = 7):
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    with _get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT thread_id FROM thread_tracker WHERE created_at < %s", (cutoff,)
            )
            old_threads = [row[0] for row in cur.fetchall()]
            for tid in old_threads:
                cur.execute("DELETE FROM checkpoint_blobs  WHERE thread_id = %s", (tid,))
                cur.execute("DELETE FROM checkpoint_writes WHERE thread_id = %s", (tid,))
                cur.execute("DELETE FROM checkpoints       WHERE thread_id = %s", (tid,))
                cur.execute("DELETE FROM thread_tracker    WHERE thread_id = %s", (tid,))
        conn.commit()
    print(f"Cleaned up {len(old_threads)} threads older than {days} days")


def delete_thread(thread_id: str):
    """Delete a thread and all its checkpoint data."""
    tid = str(thread_id)
    with _get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM checkpoint_blobs  WHERE thread_id = %s", (tid,))
            cur.execute("DELETE FROM checkpoint_writes WHERE thread_id = %s", (tid,))
            cur.execute("DELETE FROM checkpoints       WHERE thread_id = %s", (tid,))
            cur.execute("DELETE FROM thread_tracker    WHERE thread_id = %s", (tid,))
        conn.commit()
