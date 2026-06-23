from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from database import query
from auth import require_employee
from datetime import date as _date

employee_router = APIRouter(prefix="/employee", tags=["Employee"])
templates = Jinja2Templates(directory="templates")


def require_branch_manager(request: Request, session=Depends(require_employee)):
    """Only employees with position = BRANCH_MANAGER may pass."""
    if session.get("position") != "BRANCH_MANAGER":
        raise HTTPException(status_code=403, detail="Branch Manager access required.")
    return session


@employee_router.get("/dashboard", response_class=HTMLResponse)
def employee_dashboard_router(request: Request, session=Depends(require_employee)):
    """
    Generic entry point — routes by position.
    Only BRANCH_MANAGER has a built dashboard right now;
    other positions show a simple placeholder until built.
    """
    position = session.get("position")

    if position == "BRANCH_MANAGER":
        return _branch_manager_dashboard(request, session)

    return templates.TemplateResponse(request, "employee/branch_manager/dashboard.html", {
        "user_name": session.get("user_name"),
        "role":      "EMPLOYEE",
        "position":  position,
    })


@employee_router.get("/dashboard/branch_manager", response_class=HTMLResponse)
def branch_manager_dashboard_direct(request: Request, session=Depends(require_branch_manager)):
    """Direct URL — used by sidebar nav links."""
    return _branch_manager_dashboard(request, session)


def _branch_manager_dashboard(request: Request, session):
    branch_id = session.get("branch_id")

    if not branch_id:
        return templates.TemplateResponse(request, "employee/branch_manager/dashboard.html", {
            "user_name": session.get("user_name"),
            "role":      "EMPLOYEE",
            "position":  "BRANCH_MANAGER",
            "no_branch": True,
        })

    # ── Branch info ──────────────────────────────────────────────────────
    branch = query("""
        SELECT b.branch_id, b.branch_name, b.address, b.phone,
               b.open_time, b.close_time, c.city_name
        FROM   branch b JOIN city c USING (city_id)
        WHERE  b.branch_id = %s
    """, (branch_id,))
    branch = branch[0] if branch else {}

    # ── Today / this month stats ────────────────────────────────────────
    today_stats = query("""
        SELECT COUNT(*) AS n, COALESCE(SUM(total_amt),0) AS revenue
        FROM   sale
        WHERE  branch_id = %s AND DATE(sale_date) = CURRENT_DATE
    """, (branch_id,))[0]

    month_stats = query("""
        SELECT COALESCE(SUM(total_amt),0) AS revenue
        FROM   sale
        WHERE  branch_id = %s
          AND  payment_status = 'PAID'
          AND  DATE_TRUNC('month', sale_date) = DATE_TRUNC('month', CURRENT_DATE)
    """, (branch_id,))[0]

    pending_orders = query("""
        SELECT COUNT(*) AS n
        FROM   online_order
        WHERE  branch_id = %s
          AND  order_status NOT IN ('DELIVERED','CANCELLED')
    """, (branch_id,))[0]["n"]

    low_stock = query("""
        SELECT bi.inv_id, p.product_name, bi.quantity, bi.reorder_level
        FROM   branch_inventory bi
        JOIN   product p USING (product_id)
        WHERE  bi.branch_id = %s AND bi.quantity <= bi.reorder_level
        ORDER  BY bi.quantity ASC
        LIMIT  5
    """, (branch_id,))

    low_stock_count = query("""
        SELECT COUNT(*) AS n
        FROM   branch_inventory
        WHERE  branch_id = %s AND quantity <= reorder_level
    """, (branch_id,))[0]["n"]

    staff_count = query("""
        SELECT COUNT(*) AS n
        FROM   employee
        WHERE  branch_id = %s AND is_active = 'Y'
    """, (branch_id,))[0]["n"]

    # ── 7-day sales activity chart ──────────────────────────────────────
    weekly = query("""
        SELECT TO_CHAR(DATE(sale_date), 'Dy') AS day,
               COALESCE(SUM(total_amt), 0)    AS revenue
        FROM   sale
        WHERE  branch_id = %s
          AND  sale_date >= CURRENT_DATE - INTERVAL '6 day'
        GROUP  BY DATE(sale_date)
        ORDER  BY DATE(sale_date)
    """, (branch_id,))
    chart_labels = [row["day"] for row in weekly]
    chart_data   = [float(row["revenue"]) for row in weekly]

    # ── Order type breakdown (in-store vs online) this month ───────────
    breakdown = query("""
        SELECT order_type, COUNT(*) AS n, COALESCE(SUM(total_amt),0) AS revenue
        FROM   sale
        WHERE  branch_id = %s
          AND  DATE_TRUNC('month', sale_date) = DATE_TRUNC('month', CURRENT_DATE)
        GROUP  BY order_type
    """, (branch_id,))
    in_store = next((b for b in breakdown if b["order_type"] == "IN_STORE"), {"n": 0, "revenue": 0})
    online   = next((b for b in breakdown if b["order_type"] == "ONLINE"),   {"n": 0, "revenue": 0})

    # ── Monthly target progress ─────────────────────────────────────────
    # NOTE: no target table exists in the schema yet — using a flat
    # placeholder target. Replace with a real source once available.
    monthly_target = 500000  # BDT
    revenue_this_month = float(month_stats["revenue"])
    target_pct = min(100, round((revenue_this_month / monthly_target) * 100)) if monthly_target else 0

    # ── Recent sales ─────────────────────────────────────────────────────
    recent_sales = query("""
        SELECT s.sale_id, COALESCE(c.cust_name, 'Walk-in') AS customer,
               s.total_amt, s.payment_status,
               TO_CHAR(s.sale_date, 'DD Mon, HH12:MI AM') AS sale_time
        FROM   sale s
        LEFT JOIN customer c USING (cust_id)
        WHERE  s.branch_id = %s
        ORDER  BY s.sale_date DESC
        LIMIT  5
    """, (branch_id,))

    return templates.TemplateResponse(request, "employee/branch_manager/dashboard.html", {
        "user_name":        session.get("user_name"),
        "role":             "EMPLOYEE",
        "position":         "BRANCH_MANAGER",
        "no_branch":        False,
        "branch":           branch,
        "today_orders":     today_stats["n"],
        "today_revenue":    float(today_stats["revenue"]),
        "month_revenue":    revenue_this_month,
        "pending_orders":   pending_orders,
        "low_stock":        low_stock,
        "low_stock_count":  low_stock_count,
        "staff_count":      staff_count,
        "chart_labels":     chart_labels,
        "chart_data":       chart_data,
        "in_store_count":   in_store["n"],
        "in_store_revenue": float(in_store["revenue"]),
        "online_count":     online["n"],
        "online_revenue":   float(online["revenue"]),
        "target_pct":       target_pct,
        "monthly_target":   monthly_target,
        "recent_sales":     recent_sales,
    })

from fastapi import Form
from fastapi.responses import RedirectResponse
from database import execute


# ══════════════════════════════════════════════════════════════════════════════
#  BRANCH SALES
# ══════════════════════════════════════════════════════════════════════════════

@employee_router.get("/branch/sales", response_class=HTMLResponse)
def branch_sales(request: Request, session=Depends(require_branch_manager)):
    branch_id = session.get("branch_id")

    if not branch_id:
        return templates.TemplateResponse(request, "employee/branch_manager/sales.html", {
            "user_name": session.get("user_name"), "role": "EMPLOYEE",
            "position": "BRANCH_MANAGER", "no_branch": True, "sales": [],
        })

    sales = query("""
        SELECT s.sale_id,
               TO_CHAR(s.sale_date,'DD Mon YYYY HH24:MI') AS sale_date,
               s.order_type, s.subtotal, s.discount_amt, s.total_amt,
               s.payment_status, e.emp_name,
               COALESCE(c.cust_name, 'Walk-in') AS customer
        FROM   sale s
        JOIN   employee e ON s.emp_id = e.emp_id
        LEFT JOIN customer c ON s.cust_id = c.cust_id
        WHERE  s.branch_id = %s
        ORDER  BY s.sale_date DESC
    """, (branch_id,))

    return templates.TemplateResponse(request, "employee/branch_manager/sales.html", {
        "user_name": session.get("user_name"), "role": "EMPLOYEE",
        "position": "BRANCH_MANAGER", "no_branch": False, "sales": sales,
    })


# ══════════════════════════════════════════════════════════════════════════════
#  BRANCH INVENTORY
# ══════════════════════════════════════════════════════════════════════════════

# @employee_router.get("/branch/inventory", response_class=HTMLResponse)
# def branch_inventory(request: Request, session=Depends(require_branch_manager)):
#     branch_id = session.get("branch_id")

#     if not branch_id:
#         return templates.TemplateResponse(request, "employee/branch_manager/inventory.html", {
#             "user_name": session.get("user_name"), "role": "EMPLOYEE",
#             "position": "BRANCH_MANAGER", "no_branch": True, "inventory": [],
#         })

#     inventory = query("""
#         SELECT bi.inv_id, p.product_name, bi.quantity, bi.reorder_level,
#                bi.shelf_location,
#                TO_CHAR(bi.last_restocked, 'DD Mon YYYY') AS last_restocked,
#                CASE WHEN bi.quantity <= bi.reorder_level THEN 'LOW' ELSE 'OK' END AS stock_status
#         FROM   branch_inventory bi
#         JOIN   product p USING (product_id)
#         WHERE  bi.branch_id = %s
#         ORDER  BY p.product_name
#     """, (branch_id,))

#     return templates.TemplateResponse(request, "employee/branch_manager/inventory.html", {
#         "user_name": session.get("user_name"), "role": "EMPLOYEE",
#         "position": "BRANCH_MANAGER", "no_branch": False, "inventory": inventory,
#     })


# ══════════════════════════════════════════════════════════════════════════════
#  BRANCH ONLINE ORDERS
# ══════════════════════════════════════════════════════════════════════════════

@employee_router.get("/branch/orders", response_class=HTMLResponse)
def branch_orders(request: Request, session=Depends(require_branch_manager)):
    branch_id = session.get("branch_id")

    if not branch_id:
        return templates.TemplateResponse(request, "employee/branch_manager/orders.html", {
            "user_name": session.get("user_name"), "role": "EMPLOYEE",
            "position": "BRANCH_MANAGER", "no_branch": True, "orders": [],
        })

    orders = query("""
        SELECT o.order_id, c.cust_name, o.order_status, o.delivery_address,
               o.delivery_charge,
               TO_CHAR(o.order_date, 'DD Mon YYYY HH24:MI')        AS order_date,
               TO_CHAR(o.expected_delivery, 'DD Mon YYYY HH24:MI') AS expected_delivery,
               s.total_amt
        FROM   online_order o
        JOIN   customer c USING (cust_id)
        LEFT JOIN sale s ON o.sale_id = s.sale_id
        WHERE  o.branch_id = %s
        ORDER  BY o.order_date DESC
    """, (branch_id,))

    return templates.TemplateResponse(request, "employee/branch_manager/orders.html", {
        "user_name": session.get("user_name"), "role": "EMPLOYEE",
        "position": "BRANCH_MANAGER", "no_branch": False, "orders": orders,
    })


@employee_router.post("/branch/orders/update-status")
def update_order_status(
    request:      Request,
    order_id:     str = Form(...),
    order_status: str = Form(...),
    session=Depends(require_branch_manager),
):
    branch_id = session.get("branch_id")

    # Only allow updating orders that belong to this manager's own branch
    existing = query(
        "SELECT 1 FROM online_order WHERE order_id = %s AND branch_id = %s",
        (order_id, branch_id)
    )
    if not existing:
        return RedirectResponse(
            "/employee/branch/orders?error=Order+not+found+for+your+branch",
            status_code=302
        )

    execute(
        "UPDATE online_order SET order_status = %s WHERE order_id = %s",
        (order_status, order_id)
    )

    return RedirectResponse(
        f"/employee/branch/orders?success=Order+{order_id}+updated",
        status_code=302
    )

#employee

@employee_router.get("/branch/staff", response_class=HTMLResponse)
def employees_page(request: Request, session=Depends(require_branch_manager)):
    employees = query("""
        SELECT e.emp_id,
               e.emp_name,
               e.email,
               e.phone,
               e.position,
               e.salary,
               e.hire_date,
               e.gender,
               e.is_active,
               d.dept_name
        FROM employee e
        LEFT JOIN branch b
            ON e.branch_id = b.branch_id
        LEFT JOIN department d
            ON e.dept_id = d.dept_id
        WHERE e.branch_id = %s
        ORDER BY e.emp_name
    """, (session.get("branch_id"),))

    return templates.TemplateResponse(
        request,
        "employee/branch_manager/staffs.html",
        {
            "employees": employees,
            "user_name": session.get("user_name"),
            "role": "EMPLOYEE",
            "position": "BRANCH_MANAGER"
        }
    )

# ══════════════════════════════════════════════════════════════════════════════
#  BRANCH INVENTORY  — Add / Edit / Delete routes
#  Paste these into employee_router (employee.py) alongside the existing
#  branch_inventory GET route.
# ══════════════════════════════════════════════════════════════════════════════



# ── GET  /employee/branch/inventory  (enhanced — passes extra context) ────────

@employee_router.get("/branch/inventory", response_class=HTMLResponse)
def branch_inventory(request: Request, session=Depends(require_branch_manager)):
    branch_id = session.get("branch_id")

    if not branch_id:
        return templates.TemplateResponse(request, "employee/branch_manager/inventory.html", {
            "user_name": session.get("user_name"), "role": "EMPLOYEE",
            "position": "BRANCH_MANAGER", "no_branch": True,
            "inventory": [], "available_products": [], "categories": [],
        })

    # ── Current inventory ────────────────────────────────────────────────
    inventory = query("""
        SELECT bi.inv_id,
               p.product_name,
               bi.quantity,
               bi.reorder_level,
               bi.shelf_location,
               TO_CHAR(bi.last_restocked, 'DD Mon YYYY')  AS last_restocked,
               bi.last_restocked::text                    AS last_restocked_raw,
               CASE WHEN bi.quantity <= bi.reorder_level
                    THEN 'LOW' ELSE 'OK' END              AS stock_status
        FROM   branch_inventory bi
        JOIN   product p USING (product_id)
        WHERE  bi.branch_id = %s
        ORDER  BY p.product_name
    """, (branch_id,))

    # ── Products NOT yet in this branch's inventory (for Add modal) ───────
    available_products = query("""
        SELECT p.product_id, p.product_name, p.unit_price, p.unit, p.cat_id
        FROM   product p
        WHERE  p.is_active = 'Y'
          AND  p.product_id NOT IN (
              SELECT product_id FROM branch_inventory WHERE branch_id = %s
          )
        ORDER  BY p.product_name
    """, (branch_id,))

    # ── All categories (for the cascade filter in Add modal) ──────────────
    categories = query("""
        SELECT cat_id, cat_name
        FROM   category
        ORDER  BY cat_name
    """, ())

    return templates.TemplateResponse(request, "employee/branch_manager/inventory.html", {
        "user_name":          session.get("user_name"),
        "role":               "EMPLOYEE",
        "position":           "BRANCH_MANAGER",
        "no_branch":          False,
        "inventory":          inventory,
        "available_products": available_products,
        "categories":         categories,
    })


# ── POST  /employee/branch/inventory/add ─────────────────────────────────────

@employee_router.post("/branch/inventory/add")
def add_inventory(
    request:        Request,
    product_id:     str           = Form(...),
    quantity:       float         = Form(...),
    reorder_level:  float         = Form(...),
    shelf_location: str           = Form(""),
    last_restocked: str | None    = Form(None),
    session=Depends(require_branch_manager),
):
    branch_id = session.get("branch_id")

    # Safety: confirm product not already tracked for this branch
    exists = query(
        "SELECT 1 FROM branch_inventory WHERE branch_id = %s AND product_id = %s",
        (branch_id, product_id)
    )
    if exists:
        return RedirectResponse(
            "/employee/branch/inventory?error=Product+already+exists+in+inventory",
            status_code=302
        )

    # Generate next inv_id  (I-001, I-002, …)
    max_id = query("SELECT MAX(inv_id) AS mx FROM branch_inventory", ())
    mx = max_id[0]["mx"] or "I-000"
    next_num = int(mx.split("-")[1]) + 1
    inv_id = f"I-{next_num:05d}"

    execute("""
        INSERT INTO branch_inventory
               (inv_id, branch_id, product_id, quantity, reorder_level,
                shelf_location, last_restocked)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, (
        inv_id, branch_id, product_id, quantity, reorder_level,
        shelf_location or None,
        last_restocked or str(_date.today()),   # default to today if blank
    ))

    return RedirectResponse(
        f"/employee/branch/inventory?success=Item+{inv_id}+added+to+inventory",
        status_code=302
    )


# ── POST  /employee/branch/inventory/edit ────────────────────────────────────

@employee_router.post("/branch/inventory/edit")
def edit_inventory(
    request:        Request,
    inv_id:         str           = Form(...),
    quantity:       float         = Form(...),
    reorder_level:  float         = Form(...),
    shelf_location: str           = Form(""),
    last_restocked: str | None    = Form(None),
    session=Depends(require_branch_manager),
):
    branch_id = session.get("branch_id")

    # Verify the record belongs to this manager's branch
    existing = query(
        "SELECT 1 FROM branch_inventory WHERE inv_id = %s AND branch_id = %s",
        (inv_id, branch_id)
    )
    if not existing:
        return RedirectResponse(
            "/employee/branch/inventory?error=Record+not+found+for+your+branch",
            status_code=302
        )

    # If last_restocked comes through blank (shouldn't happen with JS default,
    # but defensive fallback: fetch and preserve the existing DB value)
    if not last_restocked:
        existing_date = query(
            "SELECT last_restocked::text AS d FROM branch_inventory WHERE inv_id = %s",
            (inv_id,)
        )
        last_restocked = (existing_date[0]["d"] or str(_date.today()))[:10] if existing_date else str(_date.today())

    execute("""
        UPDATE branch_inventory
        SET    quantity        = %s,
               reorder_level  = %s,
               shelf_location = %s,
               last_restocked = %s
        WHERE  inv_id = %s
    """, (
        quantity, reorder_level,
        shelf_location or None,
        last_restocked,
        inv_id,
    ))

    return RedirectResponse(
        f"/employee/branch/inventory?success=Inventory+{inv_id}+updated",
        status_code=302
    )


# ── POST  /employee/branch/inventory/delete ───────────────────────────────────

@employee_router.post("/branch/inventory/delete")
def delete_inventory(
    request:    Request,
    inv_id:     str = Form(...),
    confirm_id: str = Form(...),
    session=Depends(require_branch_manager),
):
    branch_id = session.get("branch_id")

    # Typed confirmation must match
    if confirm_id.strip() != inv_id.strip():
        return RedirectResponse(
            "/employee/branch/inventory?error=Confirmation+ID+did+not+match",
            status_code=302
        )

    # Verify ownership
    existing = query(
        "SELECT 1 FROM branch_inventory WHERE inv_id = %s AND branch_id = %s",
        (inv_id, branch_id)
    )
    if not existing:
        return RedirectResponse(
            "/employee/branch/inventory?error=Record+not+found+for+your+branch",
            status_code=302
        )

    execute(
        "DELETE FROM branch_inventory WHERE inv_id = %s",
        (inv_id,)
    )

    return RedirectResponse(
        f"/employee/branch/inventory?success=Inventory+record+{inv_id}+deleted",
        status_code=302
    )