from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.templating import Jinja2Templates
from auth import require_employee
from datetime import date as _date
import json
from datetime import datetime
from fastapi import APIRouter, Request, Depends, Form, Query
from fastapi.responses import HTMLResponse, JSONResponse
from database import query, execute
from auth import _hash, _verify

employee_router = APIRouter(prefix="/employee", tags=["Employee"])
templates = Jinja2Templates(directory="templates")


def require_branch_manager(request: Request, session=Depends(require_employee)):
    """Only employees with position = BRANCH_MANAGER may pass."""
    if session.get("position") != "BRANCH_MANAGER":
        raise HTTPException(status_code=403, detail="Branch Manager access required.")
    return session


@employee_router.get("/branch/dashboard", response_class=HTMLResponse)
def employee_dashboard_router(request: Request, session=Depends(require_employee)):
    """
    Generic entry point — routes by position.
    Only BRANCH_MANAGER has a built dashboard right now;
    other positions show a simple placeholder until built.
    """
    position = session.get("position")

    if position == "BRANCH_MANAGER":
        return _branch_manager_dashboard(request, session)
    
    elif position == "CASHIER":
        return RedirectResponse(
            url="/employee/cashier/dashboard",
            status_code=302
        )
    
    elif position == "DELIVERY_RIDER":
        return RedirectResponse(
            url="/employee/delivery_rider/dashboard",
            status_code=302
        )
    
    elif position == "SALES_STAFF":
        return RedirectResponse(
            url="/employee/sales_staff/dashboard",
            status_code=302
        )

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


"""
Cashier POS routes — add to employee.py (inside employee_router)

Endpoints:
  GET  /employee/cashier/dashboard        → POS page
  GET  /employee/cashier/lookup?phone=…   → JSON customer lookup
  POST /employee/cashier/sale/submit      → Create sale, return JSON receipt
"""


# ── Re-use the employee_router already defined in employee.py ──────────────
# (paste these routes into the existing employee.py file)


def require_cashier(request: Request, session=Depends(require_employee)):
    """Only CASHIER employees may pass."""
    if session.get("position") != "CASHIER":
        raise HTTPException(status_code=403, detail="Cashier access required.")
    return session


# ══════════════════════════════════════════════════════════════════════════════
#  GET  /employee/cashier/dashboard  — POS page
# ══════════════════════════════════════════════════════════════════════════════

@employee_router.get("/cashier/dashboard", response_class=HTMLResponse)
def cashier_dashboard(request: Request, session=Depends(require_cashier)):
    branch_id = session.get("branch_id")

    # Branch info for receipt header
    branch_row = query("""
        SELECT b.branch_name, c.city_name
        FROM   branch b JOIN city c USING (city_id)
        WHERE  b.branch_id = %s
    """, (branch_id,))
    branch_name = branch_row[0]["branch_name"] if branch_row else "Branch"

    # All in-stock products for this branch with active discount if any
    inventory = query("""
        SELECT bi.inv_id,
               p.product_id,
               p.product_name,
               p.unit_price,
               p.unit,
               bi.quantity,
               bi.reorder_level,
               d.discount_id,
               d.discount_value  AS disc_value,
               d.discount_type   AS disc_type
        FROM   branch_inventory bi
        JOIN   product p USING (product_id)
        LEFT JOIN discount d
               ON  (d.product_id = p.product_id OR d.cat_id = p.cat_id)
               AND CURRENT_DATE BETWEEN d.start_date AND d.end_date
        WHERE  bi.branch_id = %s
          AND  bi.quantity   > 0
          AND  p.is_active   = 'Y'
        ORDER BY p.product_name
    """, (branch_id,))

    return templates.TemplateResponse(request, "employee/cashier/pos.html", {
        "user_name":   session.get("user_name"),
        "role":        "EMPLOYEE",
        "position":    "CASHIER",
        "branch_name": branch_name,
        "inventory":   inventory,
    })


# ══════════════════════════════════════════════════════════════════════════════
#  GET  /employee/cashier/lookup?phone=…  — customer lookup (JSON)
# ══════════════════════════════════════════════════════════════════════════════

@employee_router.get("/cashier/lookup")
def cashier_lookup(
    phone:   str = Query(...),
    session=Depends(require_cashier),
):
    rows = query("""
        SELECT cust_id, cust_name, membership_type, loyalty_points
        FROM   customer
        WHERE  phone = %s
    """, (phone.strip(),))

    if rows:
        c = rows[0]
        return JSONResponse({
            "found":      True,
            "cust_id":    c["cust_id"],
            "name":       c["cust_name"],
            "membership": c["membership_type"],
            "points":     int(c["loyalty_points"]),
        })
    return JSONResponse({"found": False})


# ══════════════════════════════════════════════════════════════════════════════
#  POST /employee/cashier/sale/submit  — complete the sale (JSON response)
# ══════════════════════════════════════════════════════════════════════════════

@employee_router.post("/cashier/sale/submit")
async def submit_sale(
    request:        Request,
    cust_id:        str  = Form(""),
    cust_phone:     str  = Form(""),
    cust_name:      str  = Form(""),
    is_new_cust:    str  = Form("0"),
    payment_method: str  = Form("CASH"),
    cart_json:      str  = Form(...),
    note:           str  = Form(""),
    session=Depends(require_cashier),
):
    branch_id = session.get("branch_id")
    emp_id    = session.get("user_id")   # cashier's employee id stored in session

    # ── 1. Parse cart ────────────────────────────────────────────────────────
    try:
        cart = json.loads(cart_json)
    except Exception:
        return JSONResponse({"error": "Invalid cart data."}, status_code=400)

    if not cart:
        return JSONResponse({"error": "Cart is empty."}, status_code=400)

    # ── 2. Resolve / create customer ─────────────────────────────────────────
    final_cust_id = cust_id.strip() or None

    if is_new_cust == "1" and cust_phone.strip():
        # Final server-side phone check (guards against stale JS state / race conditions)
        phone_check = query(
            "SELECT cust_id FROM customer WHERE phone = %s",
            (cust_phone.strip(),)
        )
        if phone_check:
            # Phone already registered — use that customer instead of inserting
            final_cust_id = phone_check[0]["cust_id"]
        else:
            # Safe to enroll — use numeric-only MAX to avoid non-numeric suffixes
            max_row = query("""
                SELECT MAX(CAST(SUBSTRING(cust_id FROM 3) AS INTEGER)) AS mx
                FROM   customer
                WHERE  cust_id ~ '^C-[0-9]+$'
            """, ())
            next_n  = (max_row[0]["mx"] or 0) + 1
            new_id  = f"C-{next_n:05d}"

            name_to_use = cust_name.strip() or "Walk-in"

            execute("""
                INSERT INTO customer
                    (cust_id, cust_name, email, phone, join_date, membership_type)
                VALUES (%s, %s, NULL, %s, CURRENT_DATE, 'REGULAR')
            """, (new_id, name_to_use, cust_phone.strip()))

            final_cust_id = new_id

    # ── 3. Generate sale_id (numeric-only MAX — avoids S-ON010 style IDs) ──────
    max_sale = query("""
        SELECT MAX(CAST(SUBSTRING(sale_id FROM 3) AS INTEGER)) AS mx
        FROM   sale
        WHERE  sale_id ~ '^S-[0-9]+$'
    """, ())
    next_s  = (max_sale[0]["mx"] or 0) + 1
    sale_id = f"S-{next_s:06d}"

    # ── 4. Calculate totals ──────────────────────────────────────────────────
    subtotal     = 0.0
    discount_amt = 0.0
    items_out    = []   # for receipt

    for item in cart:
        product_id = item["product_id"]
        inv_id     = item["inv_id"]
        qty        = float(item["qty"])
        unit_price = float(item["unit_price"])
        disc_id    = item.get("disc_id") or None
        disc_value = float(item.get("disc_value") or 0)
        disc_type  = item.get("disc_type") or ""

        line_sub  = unit_price * qty
        line_disc = 0.0
        if disc_value and disc_type == "PERCENT":
            line_disc = (unit_price * disc_value / 100) * qty
        elif disc_value and disc_type == "FLAT":
            line_disc = min(disc_value, unit_price) * qty

        line_total = line_sub - line_disc
        subtotal     += line_sub
        discount_amt += line_disc

        # Verify stock still available
        stock_row = query(
            "SELECT quantity FROM branch_inventory WHERE inv_id = %s AND branch_id = %s",
            (inv_id, branch_id)
        )
        if not stock_row or float(stock_row[0]["quantity"]) < qty:
            # Fetch product name for friendly error
            p_name = query("SELECT product_name FROM product WHERE product_id = %s",
                           (product_id,))
            name   = p_name[0]["product_name"] if p_name else product_id
            return JSONResponse(
                {"error": f"Insufficient stock for '{name}'. Please refresh and retry."},
                status_code=409
            )

        items_out.append({
            "product_id": product_id,
            "inv_id":     inv_id,
            "qty":        qty,
            "unit_price": unit_price,
            "disc_id":    disc_id,
            "line_total": line_total,
            "name":       item.get("name", product_id),
        })

    total_amt = subtotal - discount_amt

    # ── 5. Insert sale ───────────────────────────────────────────────────────
    execute("""
        INSERT INTO sale
            (sale_id, branch_id, cust_id, emp_id, order_type,
             subtotal, discount_amt, tax_amt, total_amt, payment_status)
        VALUES (%s, %s, %s, %s, 'IN_STORE', %s, %s, 0, %s, 'PAID')
    """, (
        sale_id, branch_id, final_cust_id, emp_id,
        round(subtotal, 2), round(discount_amt, 2), round(total_amt, 2)
    ))

    # ── 6. Insert sale_items + deduct inventory ──────────────────────────────
    for item in items_out:
        execute("""
            INSERT INTO sale_item
                (sale_id, product_id, quantity, unit_price, discount_id, line_total)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            sale_id, item["product_id"], item["qty"],
            item["unit_price"], item["disc_id"], round(item["line_total"], 2)
        ))

        # Deduct from branch_inventory
        execute("""
            UPDATE branch_inventory
            SET    quantity = quantity - %s
            WHERE  inv_id   = %s
        """, (item["qty"], item["inv_id"]))

    # ── 7. Record payment (numeric-only MAX) ─────────────────────────────────
    max_pay = query("""
        SELECT MAX(CAST(SUBSTRING(payment_id FROM 5) AS INTEGER)) AS mx
        FROM   payment
        WHERE  payment_id ~ '^PAY-[0-9]+$'
    """, ())
    next_p  = (max_pay[0]["mx"] or 0) + 1
    pay_id  = f"PAY-{next_p:04d}"

    execute("""
        INSERT INTO payment
            (payment_id, sale_id, amount, method, reference_no, status)
        VALUES (%s, %s, %s, %s, %s, 'SUCCESS')
    """, (
        pay_id, sale_id, round(total_amt, 2),
        payment_method,
        note.strip() or None,
    ))

    # ── 8. Update loyalty points (1 point per 10 BDT spent) ─────────────────
    if final_cust_id:
        points_earned = int(total_amt // 10)
        if points_earned > 0:
            execute("""
                UPDATE customer
                SET loyalty_points = loyalty_points + %s
                WHERE cust_id = %s
            """, (points_earned, final_cust_id))

    # ── 9. Build receipt payload ─────────────────────────────────────────────
    customer_display = "Walk-in"
    if final_cust_id:
        cust_row = query("SELECT cust_name FROM customer WHERE cust_id = %s",
                         (final_cust_id,))
        if cust_row:
            customer_display = cust_row[0]["cust_name"]

    return JSONResponse({
        "sale_id":        sale_id,
        "date":           datetime.now().strftime("%d %b %Y, %I:%M %p"),
        "customer":       customer_display,
        "cashier":        session.get("user_name", "Cashier"),
        "payment_method": payment_method,
        "subtotal":       round(subtotal, 2),
        "discount":       round(discount_amt, 2),
        "total":          round(total_amt, 2),
        "items": [
            {
                "name":       i["name"],
                "qty":        i["qty"],
                "unit_price": i["unit_price"],
                "line_total": i["line_total"],
            }
            for i in items_out
        ],
    })


@employee_router.get("/cashier/sales", response_class=HTMLResponse)
def branch_sales(request: Request, session=Depends(require_cashier)):
    branch_id = session.get("branch_id")

    if not branch_id:
        return templates.TemplateResponse(request, "employee/cashier/sales.html", {
            "user_name": session.get("user_name"), "role": "EMPLOYEE",
            "position": "CASHIER", "no_branch": True, "sales": [],
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
        AND s.order_type = 'IN_STORE'
        ORDER  BY s.sale_date DESC
    """, (branch_id,))

    return templates.TemplateResponse(request, "employee/cashier/sales.html", {
        "user_name": session.get("user_name"), "role": "EMPLOYEE",
        "position": "CASHIER", "no_branch": False, "sales": sales,
    })

# ════════════════════════════════════════════════════════════════════════
# GET /employee/cashier/bill/{sale_id}
# Returns full receipt JSON
# ════════════════════════════════════════════════════════════════════════

@employee_router.get("/cashier/bill/{sale_id}")
def get_bill(
    sale_id: str,
    session=Depends(require_cashier or require_branch_manager)
):
    # ── Sale header ─────────────────────────────────────────────────────
    sale = query("""
        SELECT
            s.sale_id,
            TO_CHAR(s.sale_date,'DD Mon YYYY HH24:MI') AS sale_date,
            s.order_type,
            s.subtotal,
            s.discount_amt,
            s.tax_amt,
            s.total_amt,
            s.payment_status,

            b.branch_name,

            COALESCE(c.cust_name,'Walk-in') AS customer,
            c.membership_type,

            e.emp_name AS cashier,

            py.method AS payment_method

        FROM sale s
        JOIN branch b
            ON s.branch_id = b.branch_id

        LEFT JOIN customer c
            ON s.cust_id = c.cust_id

        JOIN employee e
            ON s.emp_id = e.emp_id

        LEFT JOIN payment py
            ON s.sale_id = py.sale_id

        WHERE s.sale_id = %s
    """, (sale_id,))

    if not sale:
        return JSONResponse(
            {"error": "Sale not found"},
            status_code=404
        )

    sale = sale[0]

    # ── Items ──────────────────────────────────────────────────────────
    items = query("""
        SELECT
            p.product_name,
            p.unit,

            si.quantity,
            si.unit_price,
            si.line_total,

            d.discount_name,
            d.discount_type,
            d.discount_value

        FROM sale_item si

        JOIN product p
            ON si.product_id = p.product_id

        LEFT JOIN discount d
            ON si.discount_id = d.discount_id

        WHERE si.sale_id = %s

        ORDER BY p.product_name
    """, (sale_id,))

    formatted_items = []

    for item in items:
        disc_display = ""

        if item["discount_name"]:
            if item["discount_type"] == "PERCENT":
                disc_display = f"{item['discount_value']}%"
            else:
                disc_display = f"৳{float(item['discount_value']):.2f}"

        formatted_items.append({
            "product_name": item["product_name"],
            "unit": item["unit"],
            "quantity": float(item["quantity"]),
            "unit_price": float(item["unit_price"]),
            "line_total": float(item["line_total"]),
            "discount_name": item["discount_name"],
            "disc_display": disc_display
        })

    # ── Loyalty points earned ──────────────────────────────────────────
    loyalty_earned = int(float(sale["total_amt"]) // 10)

    return JSONResponse({
        "sale_id": sale["sale_id"],
        "sale_date": sale["sale_date"],
        "branch_name": sale["branch_name"],
        "customer": sale["customer"],
        "membership": sale["membership_type"],
        "cashier": sale["cashier"],
        "order_type": sale["order_type"],
        "payment_status": sale["payment_status"],
        "payment_method": sale["payment_method"],

        "subtotal": float(sale["subtotal"] or 0),
        "discount_amt": float(sale["discount_amt"] or 0),
        "tax_amt": float(sale["tax_amt"] or 0),
        "total_amt": float(sale["total_amt"] or 0),

        "loyalty_earned": loyalty_earned,

        "items": formatted_items
    })
# ══════════════════════════════════════════════════════════════════════════════
#  EMPLOYEE PROFILE — replace the existing employee_profile() with this version,
#  and add the two POST routes below it. Paste into employee.py.
# ══════════════════════════════════════════════════════════════════════════════

@employee_router.get("/profile", response_class=HTMLResponse)
def employee_profile(
    request: Request,
    session=Depends(require_employee)
):
    employee = query("""
        SELECT
            e.emp_id,
            e.emp_name,
            e.email,
            e.is_active,
            e.position,
            TO_CHAR(e.hire_date, 'DD Mon YYYY') AS hire_date,
            d.dept_name
        FROM employee e
        LEFT JOIN department d ON e.dept_id = d.dept_id
        WHERE e.emp_id = %s
    """, (session["user_id"],))

    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    return templates.TemplateResponse(
        request,
        "employee/profile.html",
        {
            "employee": employee[0],
            "user_name": session.get("user_name"),
            "role": "EMPLOYEE",
            "position": session.get("position")
        }
    )


# ── POST  /employee/profile/update  — name / email ───────────────────────────

@employee_router.post("/profile/update")
def employee_profile_update(
    request:  Request,
    emp_name: str = Form(...),
    email:    str = Form(...),
    session=Depends(require_employee),
):
    emp_id = session.get("user_id")

    # email is UNIQUE on the employee table — block collisions with other staff
    dup = query(
        "SELECT 1 FROM employee WHERE email = %s AND emp_id != %s",
        (email.strip(), emp_id)
    )
    if dup:
        return RedirectResponse(
            "/employee/profile?error=That+email+is+already+in+use",
            status_code=302
        )

    execute(
        "UPDATE employee SET emp_name = %s, email = %s WHERE emp_id = %s",
        (emp_name.strip(), email.strip(), emp_id)
    )

    return RedirectResponse(
        "/employee/profile?success=Profile+updated+successfully",
        status_code=302
    )


# ── POST  /employee/profile/password  — change login password ───────────────
#
# NOTE: password_hash lives on app_user (role='EMPLOYEE', ref_id=emp_id),
# not on the employee table itself — per your schema's auth design.
#
# Add this import near the top of employee.py, alongside the existing
# `from auth import require_employee` line:
#
#     from auth import require_employee, _hash, _verify

@employee_router.post("/profile/password")
def employee_profile_password(
    request:          Request,
    current_password: str = Form(...),
    new_password:      str = Form(...),
    confirm_password:  str = Form(...),
    session=Depends(require_employee),
):
    emp_id = session.get("user_id")

    if new_password != confirm_password:
        return RedirectResponse(
            "/employee/profile?error=New+passwords+do+not+match",
            status_code=302
        )
    if len(new_password) < 8:
        return RedirectResponse(
            "/employee/profile?error=Password+must+be+at+least+8+characters",
            status_code=302
        )

    user_row = query(
        "SELECT user_id, password_hash FROM app_user WHERE role = 'EMPLOYEE' AND ref_id = %s",
        (emp_id,)
    )
    if not user_row:
        return RedirectResponse(
            "/employee/profile?error=Login+account+not+found",
            status_code=302
        )

    if not _verify(current_password, user_row[0]["password_hash"]):
        return RedirectResponse(
            "/employee/profile?error=Current+password+is+incorrect",
            status_code=302
        )

    execute(
        "UPDATE app_user SET password_hash = %s WHERE user_id = %s",
        (_hash(new_password), user_row[0]["user_id"])
    )

    return RedirectResponse(
        "/employee/profile?success=Password+updated+successfully",
        status_code=302
    )

# ══════════════════════════════════════════════════════════════════════════════
#  SALES STAFF — Products page
#  Paste into employee.py alongside the existing routes.
# ══════════════════════════════════════════════════════════════════════════════


def require_sales_staff(request: Request, session=Depends(require_employee)):
    """Only SALES_STAFF employees may pass."""
    if session.get("position") != "SALES_STAFF":
        raise HTTPException(status_code=403, detail="Sales Staff access required.")
    return session


@employee_router.get("/sales_staff/dashboard", response_class=HTMLResponse)
def sales_staff_products(request: Request, session=Depends(require_sales_staff)):
    branch_id = session.get("branch_id")

    if not branch_id:
        return templates.TemplateResponse(request, "employee/sales_staff/products.html", {
            "user_name": session.get("user_name"),
            "role":      "EMPLOYEE",
            "position":  "SALES_STAFF",
            "products":  [],
            "categories": [],
        })

    # ── Products in this branch's inventory, enriched with active discount ──
    products = query("""
        SELECT
            p.product_id,
            p.product_name,
            p.brand,
            p.unit_price,
            p.unit,
            bi.quantity,
            bi.reorder_level,
            bi.shelf_location,
            cat.cat_name,

            -- Active discount (if any)
            d.discount_id,
            d.discount_name    AS disc_name,
            d.discount_type    AS disc_type,
            d.discount_value   AS disc_value,
            TO_CHAR(d.end_date, 'DD Mon YYYY') AS disc_end,

            -- Computed stock status
            CASE
                WHEN bi.quantity = 0                    THEN 'OUT'
                WHEN bi.quantity <= bi.reorder_level    THEN 'LOW'
                ELSE 'OK'
            END AS stock_status

        FROM   branch_inventory bi
        JOIN   product   p   USING (product_id)
        LEFT JOIN category cat ON p.cat_id = cat.cat_id
        LEFT JOIN discount d
               ON  (d.product_id = p.product_id OR d.cat_id = p.cat_id)
               AND CURRENT_DATE BETWEEN d.start_date AND d.end_date
        WHERE  bi.branch_id = %s
          AND  p.is_active  = 'Y'
        ORDER  BY p.product_name
    """, (branch_id,))

    # Attach a boolean convenience flag for the template
    for p in products:
        p["has_discount"] = bool(p.get("disc_value"))

    # ── Distinct categories present in this branch (for filter dropdown) ───
    categories = query("""
        SELECT DISTINCT cat.cat_id, cat.cat_name
        FROM   branch_inventory bi
        JOIN   product  p   USING (product_id)
        JOIN   category cat ON p.cat_id = cat.cat_id
        WHERE  bi.branch_id = %s
          AND  p.is_active  = 'Y'
          AND  cat.cat_name IS NOT NULL
        ORDER  BY cat.cat_name
    """, (branch_id,))

    return templates.TemplateResponse(request, "employee/sales_staff/products.html", {
        "user_name":  session.get("user_name"),
        "role":       "EMPLOYEE",
        "position":   "SALES_STAFF",
        "products":   products,
        "categories": categories,
    })


# ══════════════════════════════════════════════════════════════════════════════
#  DELIVERY RIDER — My Deliveries page
#  Paste into employee.py alongside the existing routes.
# ══════════════════════════════════════════════════════════════════════════════


def require_rider(request: Request, session=Depends(require_employee)):
    """Only DELIVERY_RIDER employees may pass."""
    if session.get("position") != "DELIVERY_RIDER":
        raise HTTPException(status_code=403, detail="Delivery Rider access required.")
    return session


# ── Badge class map (avoids logic in Jinja) ─────────────────────────────────
_DELIVERY_STATUS_BADGE = {
    "ASSIGNED":    "badge-blue",
    "PICKED_UP":   "badge-yellow",
    "ON_THE_WAY":  "badge-orange",
    "DELIVERED":   "badge-green",
    "FAILED":      "badge-red",
}


@employee_router.get("/delivery_rider/dashboard", response_class=HTMLResponse)
def rider_deliveries(request: Request, session=Depends(require_rider)):
    rider_id = session.get("user_id")   # emp_id stored in session

    # ── All deliveries assigned to this rider ───────────────────────────────
    deliveries = query("""
        SELECT
            d.delivery_id,
            d.order_id,
            d.delivery_status,
            d.distance_km,
            d.delivery_fee,
            d.rating,
            d.note,

            TO_CHAR(d.assigned_at,  'DD Mon, HH12:MI AM') AS assigned_at,
            TO_CHAR(d.picked_up_at, 'DD Mon, HH12:MI AM') AS picked_up_at,
            TO_CHAR(d.delivered_at, 'DD Mon, HH12:MI AM') AS delivered_at,

            -- For ON_THE_WAY timestamp display (no dedicated column — use assigned_at as proxy)
            CASE WHEN d.delivery_status IN ('ON_THE_WAY','DELIVERED')
                 THEN TO_CHAR(d.picked_up_at, 'DD Mon, HH12:MI AM')
                 ELSE NULL
            END AS on_the_way_at,

            -- Raw date for JS date filter
            TO_CHAR(d.assigned_at, 'Mon DD YYYY') AS assigned_date,

            -- Customer info
            c.cust_name  AS customer,
            o.delivery_address,

            -- Order total (for chip display)
            s.total_amt  AS order_total

        FROM   delivery    d
        JOIN   online_order o  ON d.order_id  = o.order_id
        JOIN   customer    c  ON o.cust_id   = c.cust_id
        LEFT JOIN sale     s  ON o.sale_id   = s.sale_id
        WHERE  d.rider_id = %s
        ORDER  BY d.assigned_at DESC
    """, (rider_id,))

    # ── Today's aggregate stats ─────────────────────────────────────────────
    stats_row = query("""
        SELECT
            COUNT(*)                                                AS total,
            COUNT(*) FILTER (WHERE delivery_status = 'ON_THE_WAY') AS on_the_way,
            COUNT(*) FILTER (WHERE delivery_status = 'PICKED_UP')  AS picked_up,
            COUNT(*) FILTER (
                WHERE delivery_status = 'DELIVERED'
                  AND DATE(delivered_at) = CURRENT_DATE
            )                                                       AS delivered,
            COALESCE(SUM(distance_km) FILTER (
                WHERE DATE(assigned_at) = CURRENT_DATE
            ), 0)                                                   AS total_km,
            ROUND(AVG(rating)::NUMERIC, 1)                          AS avg_rating
        FROM   delivery
        WHERE  rider_id = %s
    """, (rider_id,))
    stats = stats_row[0] if stats_row else {}

    return templates.TemplateResponse(request, "employee/rider/deliveries.html", {
        "user_name":    session.get("user_name"),
        "role":         "EMPLOYEE",
        "position":     "DELIVERY_RIDER",
        "deliveries":   deliveries,
        "stats":        stats,
        "status_badge": _DELIVERY_STATUS_BADGE,
    })


# ── POST  /employee/rider/update-status — advance delivery status ────────────

@employee_router.post("/rider/update-status")
def rider_update_status(
    request:    Request,
    delivery_id: str = Form(...),
    new_status:  str = Form(...),
    note:        str = Form(""),
    session=Depends(require_rider),
):
    rider_id = session.get("user_id")

    VALID_STATUSES = {"PICKED_UP", "ON_THE_WAY", "DELIVERED", "FAILED"}
    if new_status not in VALID_STATUSES:
        return RedirectResponse(
            "/employee/deliveries?error=Invalid+status+transition",
            status_code=302
        )

    # Verify this delivery belongs to this rider
    existing = query(
        "SELECT delivery_status FROM delivery WHERE delivery_id = %s AND rider_id = %s",
        (delivery_id, rider_id)
    )
    if not existing:
        return RedirectResponse(
            "/employee/deliveries?error=Delivery+not+found+or+not+assigned+to+you",
            status_code=302
        )

    current = existing[0]["delivery_status"]
    # Guard against going backwards or re-finalising
    TERMINAL = {"DELIVERED", "FAILED"}
    if current in TERMINAL:
        return RedirectResponse(
            "/employee/deliveries?error=Delivery+is+already+finalised",
            status_code=302
        )

    # Timestamp columns to fill in
    ts_col = {
        "PICKED_UP":  "picked_up_at  = CURRENT_TIMESTAMP,",
        "ON_THE_WAY": "",                            # no dedicated column in schema
        "DELIVERED":  "delivered_at  = CURRENT_TIMESTAMP,",
        "FAILED":     "",
    }.get(new_status, "")

    execute(f"""
        UPDATE delivery
        SET    {ts_col}
               delivery_status = %s,
               note            = COALESCE(NULLIF(%s, ''), note)
        WHERE  delivery_id     = %s
    """, (new_status, note.strip(), delivery_id))

    # When delivered, also update the linked online_order status
    if new_status == "DELIVERED":
        execute("""
            UPDATE online_order oo
            SET    order_status   = 'DELIVERED',
                   actual_delivery = CURRENT_TIMESTAMP
            FROM   delivery d
            WHERE  d.delivery_id = %s
              AND  d.order_id    = oo.order_id
        """, (delivery_id,))
    elif new_status == "FAILED":
        execute("""
            UPDATE online_order oo
            SET    order_status = 'CANCELLED'
            FROM   delivery d
            WHERE  d.delivery_id = %s
              AND  d.order_id    = oo.order_id
        """, (delivery_id,))

    return RedirectResponse(
        f"/employee/deliveries?success=Delivery+{delivery_id}+updated+to+{new_status.replace('_','+')}",
        status_code=302
    )