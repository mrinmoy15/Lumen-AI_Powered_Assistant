"""db/database_utils.py — PostgreSQL thread tracker for LUMEN."""
import os
import psycopg
from datetime import datetime, timedelta, timezone
from config import DATABASE_URL, PINECONE_INDEX_NAME


def _delete_pinecone_namespace(thread_id: str):
    """Delete all vectors for a thread namespace from Pinecone. Safe to call even if namespace doesn't exist."""
    try:
        from pinecone import Pinecone
        pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
        pc.Index(PINECONE_INDEX_NAME).delete(delete_all=True, namespace=str(thread_id))
    except Exception:
        pass  # namespace may not exist if no document was uploaded for this thread


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
                _delete_pinecone_namespace(tid)
                cur.execute("DELETE FROM checkpoint_blobs  WHERE thread_id = %s", (tid,))
                cur.execute("DELETE FROM checkpoint_writes WHERE thread_id = %s", (tid,))
                cur.execute("DELETE FROM checkpoints       WHERE thread_id = %s", (tid,))
                cur.execute("DELETE FROM thread_tracker    WHERE thread_id = %s", (tid,))
        conn.commit()
    print(f"Cleaned up {len(old_threads)} threads older than {days} days")


def delete_thread(thread_id: str):
    """Delete a thread and all its checkpoint data."""
    tid = str(thread_id)
    _delete_pinecone_namespace(tid)
    with _get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM checkpoint_blobs  WHERE thread_id = %s", (tid,))
            cur.execute("DELETE FROM checkpoint_writes WHERE thread_id = %s", (tid,))
            cur.execute("DELETE FROM checkpoints       WHERE thread_id = %s", (tid,))
            cur.execute("DELETE FROM thread_tracker    WHERE thread_id = %s", (tid,))
        conn.commit()
