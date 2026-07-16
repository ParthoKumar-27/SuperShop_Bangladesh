import os
import time
import psycopg2
from psycopg2.pool import ThreadedConnectionPool
from dotenv import load_dotenv
from urllib.parse import urlparse

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set in .env")

# ---------------------------------------------------
# Connection Pool
# ---------------------------------------------------
# pool = ThreadedConnectionPool(
#     minconn=1,
#     maxconn=20,
#     dsn=DATABASE_URL,
#     sslmode="require",
# )
host = urlparse(DATABASE_URL).hostname

pool_kwargs = {
    "minconn": 1,
    "maxconn": 20,
    "dsn": DATABASE_URL,
}

# Only Supabase requires SSL
if host not in ("localhost", "127.0.0.1"):
    pool_kwargs["sslmode"] = "require"

pool = ThreadedConnectionPool(**pool_kwargs)


def get_connection():
    """
    Get a PostgreSQL connection from the pool.
    """
    return pool.getconn()


def release_connection(conn):
    """
    Return the connection back to the pool.
    """
    pool.putconn(conn)


def _is_connection_dead(exc: BaseException) -> bool:
    """
    Return True if the exception indicates the pooled connection has been
    closed by the server / network (Supabase pools aggressively recycle
    idle connections).  In that case we want to drop the dead connection
    and grab a fresh one instead of returning the same broken socket to
    the pool.
    """
    if isinstance(exc, psycopg2.OperationalError):
        msg = (str(exc) or "").lower()
        return (
            "server closed the connection unexpectedly" in msg
            or "connection already closed" in msg
            or "could not connect to server" in msg
            or "connection refused" in msg
        )
    return False


def _run_with_retry(label: str, fn):
    """
    Run `fn(conn)` once.  If the connection is dead, drop it from the pool
    and retry with a fresh one.  Any other exception is propagated as-is.
    """
    last_exc = None
    for attempt in (1, 2):
        conn = get_connection()
        try:
            return fn(conn)
        except Exception as exc:
            last_exc = exc
            # Try to mark the connection as broken so psycopg2's pool
            # doesn't hand it out again.
            try:
                pool.putconn(conn, close=True)
            except Exception:
                pass
            if _is_connection_dead(exc) and attempt == 1:
                print(f"[DB] {label}: dead connection, retrying with a fresh one")
                continue
            raise
        finally:
            # On success, return the (still-healthy) connection to the pool.
            try:
                # Only release if the connection wasn't already closed
                # above (close=True).  psycopg2's putconn is a no-op when
                # the conn is already closed, but guard anyway.
                if not conn.closed:
                    release_connection(conn)
            except Exception:
                pass
    # Should be unreachable, but be explicit.
    raise last_exc  # type: ignore[misc]


def query(sql: str, params=None):
    """
    Execute a SELECT query and return rows as dictionaries.
    """
    def _run(conn):
        start = time.perf_counter()
        with conn.cursor() as cur:
            cur.execute(sql, params or ())

            if cur.description is None:
                return []

            columns = [desc[0] for desc in cur.description]
            rows = cur.fetchall()

        elapsed = (time.perf_counter() - start) * 1000
        print(f"[SQL] {elapsed:.1f} ms")
        return [dict(zip(columns, row)) for row in rows]

    return _run_with_retry("query", _run)


def execute(sql: str, params=None):
    """
    Execute INSERT / UPDATE / DELETE.
    """
    def _run(conn):
        with conn.cursor() as cur:
            cur.execute(sql, params or ())
            conn.commit()

    def _rollback(conn, exc):
        try:
            conn.rollback()
        except Exception:
            pass
        raise exc

    last_exc = None
    for attempt in (1, 2):
        conn = get_connection()
        try:
            _run(conn)
            return
        except Exception as exc:
            last_exc = exc
            _rollback(conn, exc)
            try:
                pool.putconn(conn, close=True)
            except Exception:
                pass
            if _is_connection_dead(exc) and attempt == 1:
                print("[DB] execute: dead connection, retrying with a fresh one")
                continue
            raise
        finally:
            try:
                if not conn.closed:
                    release_connection(conn)
            except Exception:
                pass
    raise last_exc  # type: ignore[misc]


def execute_returning(sql: str, params=None):
    """
    Execute INSERT ... RETURNING ...
    """
    def _run(conn):
        with conn.cursor() as cur:
            cur.execute(sql, params or ())
            row = cur.fetchone()
            conn.commit()
            if row is None:
                return None
            columns = [d[0] for d in cur.description]
            return dict(zip(columns, row))

    last_exc = None
    for attempt in (1, 2):
        conn = get_connection()
        try:
            return _run(conn)
        except Exception as exc:
            last_exc = exc
            try:
                conn.rollback()
            except Exception:
                pass
            try:
                pool.putconn(conn, close=True)
            except Exception:
                pass
            if _is_connection_dead(exc) and attempt == 1:
                print("[DB] execute_returning: dead connection, retrying with a fresh one")
                continue
            raise
        finally:
            try:
                if not conn.closed:
                    release_connection(conn)
            except Exception:
                pass
    raise last_exc  # type: ignore[misc]


def close_pool():
    """
    Close all pooled connections.
    """
    pool.closeall()