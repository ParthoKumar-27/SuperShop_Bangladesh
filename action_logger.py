import json
from decimal import Decimal
from datetime import date, datetime
from database import query, execute

class _LogEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        if isinstance(obj, (date, datetime)):
            return obj.isoformat()
        return super().default(obj)

def _next_log_id() -> str:
    last = query("SELECT log_id FROM action_log ORDER BY log_id DESC LIMIT 1")
    if last:
        n = int(last[0]["log_id"].split("-")[1])
        return f"LOG-{n + 1:06d}"
    return "LOG-000001"

def log_action(
    session: dict,
    action: str,
    table_name: str,
    record_id: str,
    description: str,
    old_values: dict | None = None,
    new_values: dict | None = None,
    request=None,
):
    execute("""
        INSERT INTO action_log
            (log_id, actor_type, actor_id, actor_name,
             action, table_name, record_id, description,
             old_values, new_values, ip_address)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        _next_log_id(),
        session.get("role"),
        session.get("user_id"),
        session.get("user_name"),
        action,
        table_name,
        record_id,
        description,
        json.dumps(old_values, cls=_LogEncoder) if old_values else None,
        json.dumps(new_values, cls=_LogEncoder) if new_values else None,
        request.client.host if request else None,
    ))