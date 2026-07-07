from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.templating import Jinja2Templates
from auth import require_employee
from datetime import date as _date
import json
from datetime import datetime
from fastapi import APIRouter, Request, Depends, Form, Query
from fastapi.responses import HTMLResponse, JSONResponse
from database import query, execute


def create_notification(recipient_type, recipient_id, notif_type, title, message,
                         branch_id=None, link_url=None, ref_table=None, ref_id=None):
    max_row = query("""
        SELECT MAX(CAST(SUBSTRING(notif_id FROM 3) AS INTEGER)) AS mx
        FROM   notification
        WHERE  notif_id ~ '^N-[0-9]+$'
    """, ())
    next_n = (max_row[0]["mx"] or 0) + 1
    notif_id = f"N-{next_n:06d}"

    execute("""
        INSERT INTO notification
            (notif_id, recipient_type, recipient_id, branch_id,
             notif_type, title, message, link_url, ref_table, ref_id)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (notif_id, recipient_type, recipient_id, branch_id,
          notif_type, title, message, link_url, ref_table, ref_id))
    return notif_id


def notify_branch_manager(branch_id, notif_type, title, message, **kw):
    mgr = query("SELECT emp_id FROM branch_manager WHERE branch_id = %s", (branch_id,))
    if mgr:
        create_notification("EMPLOYEE", mgr[0]["emp_id"], notif_type, title, message,

                            branch_id=branch_id, **kw)
        

def notify_all_branch_managers(notif_type, title, message, **kw):
    """Send the same notification to every assigned branch manager.
    Used for branch-agnostic events like a new global product being added."""
    managers = query("SELECT branch_id, emp_id FROM branch_manager", ())
    for m in managers:
        create_notification(
            "EMPLOYEE", m["emp_id"], notif_type, title, message,
            branch_id=m["branch_id"], **kw
        )


def notify_all_admins(notif_type, title, message, **kw):
    """Send the same notification to every active admin account.
    Used for events that need admin attention regardless of branch, e.g. a
    branch manager adding a new staff member who needs approval/activation."""
    admins = query("""
        SELECT admin_id
        FROM   admin_account
        WHERE  is_active = 'Y'
    """, ())
    if not admins:
        return
    for a in admins:
        create_notification(
            "ADMIN", a["admin_id"], notif_type, title, message,
            **kw,
        )

def check_low_stock(inv_id, branch_id):
    row = query("""
        SELECT bi.quantity, bi.reorder_level, p.product_name
        FROM   branch_inventory bi JOIN product p USING (product_id)
        WHERE  bi.inv_id = %s
    """, (inv_id,))[0]

    if float(row["quantity"]) <= float(row["reorder_level"]):
        existing = query("""
            SELECT 1 FROM notification
            WHERE  ref_table = 'branch_inventory' AND ref_id = %s
              AND  notif_type = 'LOW_STOCK' AND is_read = 'N'
        """, (inv_id,))
        if not existing:
            notify_branch_manager(
                branch_id, "LOW_STOCK",
                "Low stock alert",
                f"{row['product_name']} is at {row['quantity']} units (reorder level {row['reorder_level']}).",
                link_url="/employee/branch/inventory",
                ref_table="branch_inventory", ref_id=inv_id,
            )
    else:
        execute("""
            UPDATE notification SET is_read='Y', read_at=CURRENT_TIMESTAMP
            WHERE ref_table='branch_inventory' AND ref_id=%s
              AND notif_type='LOW_STOCK' AND is_read='N'
        """, (inv_id,))