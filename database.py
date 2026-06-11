import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()  # reads .env file

def get_connection():
    """Return a fresh PostgreSQL connection."""
    return psycopg2.connect(os.getenv("DATABASE_URL"))

def query(sql: str, params=None):
    """
    Run a SELECT query and return a list of dicts.
    Example:
        rows = query("SELECT * FROM product WHERE is_active = %s", ('Y',))
    """
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute(sql, params or ())
    cols = [desc[0] for desc in cur.description]
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [dict(zip(cols, row)) for row in rows]

def execute(sql: str, params=None):
    """
    Run INSERT / UPDATE / DELETE.
    Example:
        execute("UPDATE customer SET loyalty_points = %s WHERE cust_id = %s", (500, 'C-00001'))
    """
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute(sql, params or ())
    conn.commit()
    cur.close()
    conn.close()