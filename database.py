import os
import time
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


def query(sql: str, params=None):
    """
    Execute a SELECT query and return rows as dictionaries.
    """
    conn = get_connection()

    try:
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

    finally:
        release_connection(conn)


def execute(sql: str, params=None):
    """
    Execute INSERT / UPDATE / DELETE.
    """
    conn = get_connection()

    try:
        with conn.cursor() as cur:
            cur.execute(sql, params or ())
            conn.commit()

    except Exception:
        conn.rollback()
        raise

    finally:
        release_connection(conn)


def execute_returning(sql: str, params=None):
    """
    Execute INSERT ... RETURNING ...
    """
    conn = get_connection()

    try:
        with conn.cursor() as cur:
            cur.execute(sql, params or ())

            row = cur.fetchone()

            conn.commit()

            if row is None:
                return None

            columns = [d[0] for d in cur.description]

            return dict(zip(columns, row))

    except Exception:
        conn.rollback()
        raise

    finally:
        release_connection(conn)


def close_pool():
    """
    Close all pooled connections.
    """
    pool.closeall()