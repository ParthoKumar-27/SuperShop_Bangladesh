from urllib import request

from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.templating import Jinja2Templates
from httpx import request
from auth import require_employee
from datetime import date as _date
import json
from datetime import datetime
from fastapi import APIRouter, Request, Depends, Form, Query
from fastapi.responses import HTMLResponse, JSONResponse
from database import query, execute
from auth import _hash, _verify
from notifications import check_low_stock, notify_all_admins, notify_customer
employee_router = APIRouter(prefix="/employee", tags=["Employee"])
templates = Jinja2Templates(directory="templates")

def _get_branch_info(branch_id: str) -> dict:
    """Returns branch_name and branch_address for the header bar.
    Safe to call with None — returns empty strings."""
    if not branch_id:
        return {"branch_name": "", "branch_address": ""}
    row = query("""
        SELECT b.branch_name, b.address, c.city_name
        FROM   branch b JOIN city c USING (city_id)
        WHERE  b.branch_id = %s
    """, (branch_id,))
    if not row:
        return {"branch_name": "", "branch_address": ""}
    return {
        "branch_name":    row[0]["branch_name"],
        "branch_address": row[0]["address"] or row[0]["city_name"] or "",
    }

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

    # Unknown / missing position — the generic placeholder template expects
    # a half-dozen stats and the branch info, and would 500 if we just stubbed
    # them. Hand control to the global 403 handler in main.py so the user
    # sees the friendly inline notice and stays on their current page.
    raise HTTPException(
        status_code=403,
        detail="Your role doesn't have an employee dashboard yet. Please contact your admin.",
    )


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
             "branch_name": "", "branch_address": "",
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
    # NOTE: exclude CANCELLED sales from revenue & order counts — a cancelled
    # sale shouldn't count toward today's revenue or order total.
    # Combine 5 simple scalar queries into a single batch query to reduce latency
    combined_stats = query("""
        SELECT
            (SELECT COUNT(*) FROM sale WHERE branch_id=%s AND DATE(sale_date)=CURRENT_DATE AND payment_status<>'CANCELLED') AS today_n,
            (SELECT COALESCE(SUM(total_amt),0) FROM sale WHERE branch_id=%s AND DATE(sale_date)=CURRENT_DATE AND payment_status<>'CANCELLED') AS today_revenue,
            (SELECT COALESCE(SUM(total_amt),0) FROM sale WHERE branch_id=%s AND payment_status='PAID' AND DATE_TRUNC('month', sale_date) = DATE_TRUNC('month', CURRENT_DATE)) AS month_revenue,
            (SELECT COUNT(*) FROM online_order WHERE branch_id=%s AND order_status NOT IN ('DELIVERED','CANCELLED')) AS pending_orders,
            (SELECT COUNT(*) FROM branch_inventory WHERE branch_id=%s AND quantity <= reorder_level) AS low_stock_count,
            (SELECT COUNT(*) FROM employee WHERE branch_id=%s AND is_active='Y') AS staff_count
    """, (branch_id, branch_id, branch_id, branch_id, branch_id, branch_id))
    
    row = combined_stats[0] if combined_stats else {}
    
    today_stats = {"n": row.get("today_n", 0), "revenue": row.get("today_revenue", 0)}
    month_stats = {"revenue": row.get("month_revenue", 0)}
    pending_orders = row.get("pending_orders", 0)

    low_stock = query("""
        SELECT bi.inv_id, p.product_name, bi.quantity, bi.reorder_level
        FROM   branch_inventory bi
        JOIN   product p USING (product_id)
        WHERE  bi.branch_id = %s AND bi.quantity <= bi.reorder_level
        ORDER  BY bi.quantity ASC
        LIMIT  5
    """, (branch_id,))

    low_stock_count = row.get("low_stock_count", 0)
    staff_count = row.get("staff_count", 0)

    # ── 7-day sales activity chart ──────────────────────────────────────
    # Exclude CANCELLED sales so cancelled/refunded amounts don't show on the chart.
    weekly = query("""
        SELECT TO_CHAR(DATE(sale_date), 'Dy') AS day,
               COALESCE(SUM(total_amt), 0)    AS revenue
        FROM   sale
        WHERE  branch_id = %s
          AND  sale_date >= CURRENT_DATE - INTERVAL '6 day'
          AND  payment_status <> 'CANCELLED'
        GROUP  BY DATE(sale_date)
        ORDER  BY DATE(sale_date)
    """, (branch_id,))
    chart_labels = [row["day"] for row in weekly]
    chart_data   = [float(row["revenue"]) for row in weekly]

    # ── Order type breakdown (in-store vs online) this month ───────────
    # Same: exclude CANCELLED so the in-store/online counts reflect real sales.
    breakdown = query("""
        SELECT order_type, COUNT(*) AS n, COALESCE(SUM(total_amt),0) AS revenue
        FROM   sale
        WHERE  branch_id = %s
          AND  DATE_TRUNC('month', sale_date) = DATE_TRUNC('month', CURRENT_DATE)
          AND  payment_status <> 'CANCELLED'
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
        "branch_name":      branch.get("branch_name", ""),      # ← add
        "branch_address":   branch.get("address") or branch.get("city_name", ""),  # ← add
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
            "branch_name": "", "branch_address": "",
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
        **_get_branch_info(branch_id),   # ← add this line
    })



# ══════════════════════════════════════════════════════════════════════════════
#  BRANCH PRODUCTS
#  Read-only catalog of every product stocked in this manager's branch,
#  enriched with active discount info and current stock status.
#  Search by name/brand/category, filter by stock state.
# ══════════════════════════════════════════════════════════════════════════════

@employee_router.get("/branch/products", response_class=HTMLResponse)
def branch_products(request: Request,
                    session=Depends(require_branch_manager),
                    cat_id:  str = Query("",  alias="cat_id")):
    """Branch manager's product catalog — mirrors the admin products page.

    Lists every product currently stocked at this branch (joined via
    `branch_inventory`). Columns: ID, Product, Category, Supplier, Price,
    Unit, Status.  Only the category dropdown filters the list.
    """
    branch_id = session.get("branch_id")

    base_ctx = {
        "user_name":    session.get("user_name"),
        "role":         "EMPLOYEE",
        "position":     "BRANCH_MANAGER",
        "selected_cat": cat_id,
    }

    if not branch_id:
        return templates.TemplateResponse(
            request, "employee/branch_manager/products.html",
            {**base_ctx, "no_branch": True, "products": [], "categories": [],
             "total_all": 0,
             **_get_branch_info(None)}
        )

    # ── WHERE clause assembled from optional filters ─────────────────────
    # This is the **global product catalog** (everything the admin has
    # issued). Filtering is by category only; branch scoping is NOT
    # applied — the table mirrors the admin products page.
    where  = ["1=1"]
    params = []

    if cat_id == "__NONE__":
        where.append("p.cat_id IS NULL")
    elif cat_id:
        where.append("p.cat_id = %s")
        params.append(cat_id)

    where_sql = " AND ".join(where)

    products = query(f"""
        SELECT p.product_id,
               p.product_name,
               p.brand,
               p.cat_id,
               p.supplier_id,
               p.unit_price,
               p.unit,
               p.is_active,
               c.cat_name,
               s.supplier_name
        FROM   product p
        LEFT JOIN category c ON p.cat_id      = c.cat_id
        LEFT JOIN supplier s ON p.supplier_id = s.supplier_id
        WHERE  {where_sql}
        ORDER  BY p.product_name
    """, params)

    # ── All categories that exist in the catalog ─────────────────────────
    categories = query("""
        SELECT cat_id, cat_name
        FROM   category
        WHERE  cat_name IS NOT NULL
        ORDER  BY cat_name
    """)

    # ── Count per category for dropdown badges + "All" total ────────────
    cat_counts_rows = query("""
        SELECT COALESCE(cat_id, '') AS cat_id,
               COUNT(*)             AS n
        FROM   product
        GROUP BY COALESCE(cat_id, '')
    """)
    cat_counts = {row["cat_id"]: row["n"] for row in cat_counts_rows}
    total_all  = sum(cat_counts.values())

    return templates.TemplateResponse(
        request, "employee/branch_manager/products.html",
        {
            **base_ctx,
            "no_branch":  False,
            "products":   products,
            "categories": categories,
            "cat_counts": cat_counts,
            "total_all":  total_all,
            **_get_branch_info(branch_id),
        }
    )


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
            "riders": [], "branch_name": "", "branch_address": "",
        })

    orders = query("""
        SELECT o.order_id, c.cust_name, o.order_status, o.delivery_address,
               o.delivery_charge,
               TO_CHAR(o.order_date, 'DD Mon YYYY HH24:MI')        AS order_date,
               TO_CHAR(o.expected_delivery, 'DD Mon YYYY HH24:MI') AS expected_delivery,
               s.sale_id, s.total_amt,
               d.delivery_id, d.rider_id, d.delivery_status AS rider_delivery_status,
               e.emp_name AS rider_name
        FROM   online_order o
        JOIN   customer c USING (cust_id)
        LEFT JOIN sale s     ON o.sale_id  = s.sale_id
        LEFT JOIN delivery d ON o.order_id = d.order_id
        LEFT JOIN employee e ON d.rider_id = e.emp_id
        WHERE  o.branch_id = %s
        ORDER  BY o.order_date DESC
    """, (branch_id,))

    # Active riders at this branch, sorted by current workload (least busy first)
    riders = query("""
        SELECT e.emp_id, e.emp_name,
               (SELECT COUNT(*) FROM delivery dd
                WHERE dd.rider_id = e.emp_id
                  AND dd.delivery_status NOT IN ('DELIVERED', 'FAILED')) AS active_count
        FROM   employee e
        WHERE  e.branch_id = %s AND e.position = 'DELIVERY_RIDER' AND e.is_active = 'Y'
        ORDER  BY active_count ASC, e.emp_name
    """, (branch_id,))

    return templates.TemplateResponse(request, "employee/branch_manager/orders.html", {
        "user_name": session.get("user_name"), "role": "EMPLOYEE",
        "position": "BRANCH_MANAGER", "no_branch": False,
        "orders": orders, "riders": riders,
        **_get_branch_info(branch_id),
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

    if order_status == "CANCELLED":
        _cancel_and_refund(order_id)          # ← NEW

    # ── Tell the customer their order moved to a new status ────────────
    # Fire-and-forget — a notification failure must never roll back the
    # state change.  Only fire for terminal-ish statuses that matter to
    # the customer (CONFIRMED/PACKED/CANCELLED).  OUT_FOR_DELIVERY and
    # DELIVERED are owned by the rider flow downstream.
    try:
        if order_status in ("CONFIRMED", "PACKED", "CANCELLED"):
            cust_row = query(
                "SELECT cust_id FROM online_order WHERE order_id = %s",
                (order_id,),
            )
            cust_id = cust_row[0]["cust_id"] if cust_row else None
            if cust_id:
                if order_status == "CONFIRMED":
                    notify_customer(
                        cust_id, "ORDER_CONFIRMED",
                        "Order confirmed",
                        f"Your order {order_id} has been confirmed by the branch.",
                        link_url=f"/customer/dashboard",
                        ref_table="online_order", ref_id=order_id,
                    )
                elif order_status == "PACKED":
                    notify_customer(
                        cust_id, "ORDER_PACKED",
                        "Order packed",
                        f"Your order {order_id} has been packed and is ready for dispatch.",
                        link_url=f"/customer/dashboard",
                        ref_table="online_order", ref_id=order_id,
                    )
                elif order_status == "CANCELLED":
                    notify_customer(
                        cust_id, "ORDER_CANCELLED",
                        "Order cancelled",
                        f"Your order {order_id} has been cancelled by the branch. "
                        "Refund will be processed shortly.",
                        link_url=f"/customer/dashboard",
                        ref_table="online_order", ref_id=order_id,
                    )
    except Exception as _err:
        print(f"[notify] order-status customer notify failed: {_err}")

    return RedirectResponse(
        f"/employee/branch/orders?success=Order+{order_id}+updated",
        status_code=302
    )

@employee_router.post("/branch/orders/assign-rider")
def assign_rider(
    request:      Request,
    order_id:     str   = Form(...),
    rider_id:     str   = Form(...),
    distance_km:  float = Form(5.0),
    delivery_fee: float = Form(50.0),
    session=Depends(require_branch_manager),
):
    branch_id = session.get("branch_id")

    # Order must belong to this branch
    order = query(
        "SELECT order_id FROM online_order WHERE order_id = %s AND branch_id = %s",
        (order_id, branch_id)
    )
    if not order:
        return RedirectResponse(
            "/employee/branch/orders?error=Order+not+found+for+your+branch",
            status_code=302
        )

    # Prevent double-assignment (delivery.order_id is UNIQUE anyway, but fail cleanly)
    existing = query("SELECT 1 FROM delivery WHERE order_id = %s", (order_id,))
    if existing:
        return RedirectResponse(
            "/employee/branch/orders?error=This+order+already+has+a+rider+assigned",
            status_code=302
        )

    # Rider must be an active DELIVERY_RIDER at this branch
    rider_ok = query("""
        SELECT 1 FROM employee
        WHERE emp_id = %s AND branch_id = %s
          AND position = 'DELIVERY_RIDER' AND is_active = 'Y'
    """, (rider_id, branch_id))
    if not rider_ok:
        return RedirectResponse(
            "/employee/branch/orders?error=Invalid+rider+selected",
            status_code=302
        )

    # Generate next delivery_id (numeric-only MAX, format DEL-00001)
    max_row = query("""
        SELECT MAX(CAST(SUBSTRING(delivery_id FROM 5) AS INTEGER)) AS mx
        FROM   delivery
        WHERE  delivery_id ~ '^DEL-[0-9]+$'
    """, ())
    next_n = (max_row[0]["mx"] or 0) + 1
    delivery_id = f"DEL-{next_n:04d}"

    execute("""
        INSERT INTO delivery
            (delivery_id, order_id, rider_id, distance_km, delivery_fee, delivery_status)
        VALUES (%s, %s, %s, %s, %s, 'ASSIGNED')
    """, (delivery_id, order_id, rider_id, distance_km, delivery_fee))

    # NEW — this is what was missing: the fee never reached online_order before
    execute("""
        UPDATE online_order SET delivery_charge = %s WHERE order_id = %s
    """, (delivery_fee, order_id))

    # Bump the order to PACKED if it's still sitting at PLACED/CONFIRMED
    execute("""
        UPDATE online_order
        SET    order_status = 'PACKED'
        WHERE  order_id = %s AND order_status IN ('PLACED', 'CONFIRMED')
    """, (order_id,))

    # Notify the rider
    max_n = query("""
        SELECT MAX(CAST(SUBSTRING(notif_id FROM 3) AS INTEGER)) AS mx
        FROM   notification WHERE notif_id ~ '^N-[0-9]+$'
    """, ())
    notif_id = f"N-{(max_n[0]['mx'] or 0) + 1:06d}"
    execute("""
        INSERT INTO notification
            (notif_id, recipient_type, recipient_id, branch_id,
             notif_type, title, message, link_url, ref_table, ref_id)
        VALUES (%s, 'EMPLOYEE', %s, %s, 'ORDER_PLACED', %s, %s, %s, 'delivery', %s)
    """, (
        notif_id, rider_id, branch_id,
        "New delivery assigned",
        f"You've been assigned to deliver order {order_id}.",
        "/employee/delivery_rider/dashboard",
        delivery_id,
    ))

    # ── Notify the customer that a rider is on the way ────────────────
    try:
        cust_row = query(
            "SELECT cust_id FROM online_order WHERE order_id = %s",
            (order_id,),
        )
        cust_id = cust_row[0]["cust_id"] if cust_row else None
        if cust_id:
            notify_customer(
                cust_id, "RIDER_ASSIGNED",
                "Rider assigned",
                f"A rider has been assigned to your order {order_id}. "
                "They will pick it up shortly.",
                link_url="/customer/dashboard",
                ref_table="online_order", ref_id=order_id,
            )
    except Exception as _err:
        print(f"[notify] rider-assigned customer notify failed: {_err}")

    return RedirectResponse(
        f"/employee/branch/orders?success=Rider+assigned+to+{order_id}",
        status_code=302
    )


#employee
# ── REPLACE the existing employees_page GET route in employee.py with this ──

@employee_router.get("/branch/staff", response_class=HTMLResponse)
def employees_page(request: Request, session=Depends(require_branch_manager)):
    branch_id = session.get("branch_id")

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
    """, (branch_id,))

    # All departments — passed to the Add Staff modal dropdown
    departments = query("""
        SELECT dept_id, dept_name
        FROM   department
        ORDER  BY dept_name
    """, ())

    return templates.TemplateResponse(
        request,
        "employee/branch_manager/staffs.html",
        {
            "employees":   employees,
            "departments": departments,
            "user_name":   session.get("user_name"),
            "role":        "EMPLOYEE",
            "position":    "BRANCH_MANAGER",
            **_get_branch_info(branch_id),
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
            "branch_name": "", "branch_address": "",
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
        **_get_branch_info(branch_id),
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

    # Notify (or auto-clear) low-stock alert based on the new quantity/reorder_level
    check_low_stock(inv_id, branch_id)

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

    
    # Notify (or auto-clear) low-stock alert based on the new quantity/reorder_level
    check_low_stock(inv_id, branch_id)

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
        **_get_branch_info(branch_id),
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
#  GET /employee/cashier/inventory  — live inventory snapshot (JSON)
#  Called by the POS page after each sale to refresh stock numbers in the
#  product search dropdown without forcing a hard page reload.
# ══════════════════════════════════════════════════════════════════════════════

@employee_router.get("/cashier/inventory")
def cashier_inventory(session=Depends(require_cashier)):
    branch_id = session.get("branch_id")
    rows = query("""
        SELECT bi.inv_id,
               p.product_id,
               p.product_name,
               p.unit_price,
               p.unit,
               bi.quantity,
               bi.reorder_level,
               d.discount_id,
               d.discount_value AS disc_value,
               d.discount_type  AS disc_type
        FROM   branch_inventory bi
        JOIN   product p USING (product_id)
        LEFT JOIN discount d
               ON  (d.product_id = p.product_id OR d.cat_id = p.cat_id)
               AND CURRENT_DATE BETWEEN d.start_date AND d.end_date
        WHERE  bi.branch_id = %s
          AND  p.is_active  = 'Y'
        ORDER BY p.product_name
    """, (branch_id,))
    return JSONResponse([
        {
            "inv_id":      r["inv_id"],
            "product_id":  r["product_id"],
            "name":        r["product_name"],
            "price":       float(r["unit_price"]),
            "unit":        r["unit"],
            "stock":       float(r["quantity"]),
            "reorder":     float(r["reorder_level"]),
            "discount_id": r["discount_id"] or "",
            "disc_value":  float(r["disc_value"]) if r["disc_value"] is not None else 0,
            "disc_type":   r["disc_type"] or "",
        }
        for r in rows
    ])


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
    tax_amt = round(total_amt * 0.04, 2)
    total_amt = round(total_amt + tax_amt, 2)

    # ── 5. Insert sale ───────────────────────────────────────────────────────
    execute("""
        INSERT INTO sale
            (sale_id, branch_id, cust_id, emp_id, order_type,
             subtotal, discount_amt, tax_amt, total_amt, payment_status)
        VALUES (%s, %s, %s, %s, 'IN_STORE', %s, %s, %s, %s, 'PAID')
    """, (
        sale_id, branch_id, final_cust_id, emp_id,
        round(subtotal, 2), round(discount_amt, 2),
        round(tax_amt, 2), round(total_amt, 2)
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

        # Notify the branch manager if this just dropped to/under reorder level
        check_low_stock(item["inv_id"], branch_id)

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
        "tax":            tax_amt,          # ← NEW
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
            "branch_name": "", "branch_address": "",
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
        **_get_branch_info(branch_id),
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
        qty            = float(item["quantity"])
        line_total     = float(item["line_total"])
        unit_price_now = float(item["unit_price"])

        has_discount = bool(item["discount_name"]) and item["discount_value"] is not None
        disc_value   = float(item["discount_value"]) if has_discount else 0.0

        # The two sale-creation paths write sale_item differently:
        #   • IN_STORE (cashier POS): unit_price = ORIGINAL price, line_total = post-discount line
        #   • ONLINE  (customer checkout): unit_price = POST-DISCOUNT price, line_total = disc unit × qty
        # The cheaper `qty × unit_price` is, the more likely unit_price already
        # carries the original.  When qty × unit > line, treat unit_price as
        # original.  When qty × unit ≈ line, treat unit_price as the post-
        # discount unit and recover the original.
        pre_line = round(qty * unit_price_now, 2)
        unit_already_original = round(pre_line - line_total, 2) > 0.005  # discount actually applied

        if has_discount and not unit_already_original and disc_value < 100:
            # unit_price_now is the discounted unit — recover the original
            if item["discount_type"] == "PERCENT":
                original_unit = unit_price_now / (1 - disc_value / 100)
            else:
                original_unit = unit_price_now + disc_value
            original_line = original_unit * qty
        else:
            # unit_price_now is either the original (in-store) or there is no
            # discount — trust it as the original unit price.
            original_unit = unit_price_now
            original_line = pre_line

        if has_discount:
            if item["discount_type"] == "PERCENT":
                disc_display = f"{disc_value:g}%"
            else:
                disc_display = f"৳{disc_value:.2f}"

        formatted_items.append({
            "product_name":    item["product_name"],
            "unit":            item["unit"],
            "quantity":        qty,
            "unit_price":      round(original_unit, 2),
            "line_total":      round(original_line, 2),
            "discount_name":   item["discount_name"],
            "discount_value":  disc_value if has_discount else None,
            "discount_type":   item["discount_type"],
            "discounted_unit": unit_price_now,
            "discounted_line": line_total,
            "disc_display":    disc_display,
        })

    # ── Recompute totals from the live sale_item rows ─────────────────
    # The `sale` header can drift from the items (partial cancellations,
    # manual edits, etc.).  The receipt the customer sees must reflect
    # what's actually in the items table — so derive subtotal and
    # discount_amt from `formatted_items` rather than trusting sale.*.
    live_subtotal   = round(sum(i["line_total"]  for i in formatted_items), 2)
    live_discount   = round(sum(
        (i["line_total"] - i["discounted_line"]) for i in formatted_items
        if i.get("discount_name")
    ), 2)
    # Tax rate observed from the stored header so we don't hard-code 4%.
    tax_base = float(sale["subtotal"] or 0) - float(sale["discount_amt"] or 0)
    tax_rate = (float(sale["tax_amt"]) / tax_base) if tax_base > 0 else 0.04
    live_tax    = round((live_subtotal - live_discount) * tax_rate, 2)
    live_total  = round(live_subtotal - live_discount + live_tax, 2)

    # ── Loyalty points earned (1 pt per 10 BDT of the LIVE total) ────
    loyalty_earned = int(live_total // 10)

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

        "subtotal":     live_subtotal,
        "discount_amt": live_discount,
        "tax_amt":      live_tax,
        "total_amt":    live_total,

        "loyalty_earned": loyalty_earned,

        "items": formatted_items
    })


# ════════════════════════════════════════════════════════════════════════
# GET /employee/branch/order-bill/{order_id}
# Same JSON shape as the cashier bill endpoint, but resolved via
# online_order so a branch manager can pull up the receipt of any
# delivery order at their branch. Scoped to the manager's branch.
# Adds `delivery_charge` and `expected_delivery` on top of the
# standard receipt payload; `order_id` echoes the input.
# ════════════════════════════════════════════════════════════════════════

@employee_router.get("/branch/order-bill/{order_id}")
def get_order_bill(
    order_id: str,
    request:  Request,
    session=Depends(require_branch_manager),
):
    branch_id = session.get("branch_id")

    if not branch_id:
        return JSONResponse({"error": "No branch assigned"}, status_code=403)

    # ── Order header (with sale + customer + branch + rider) ─────────
    order = query("""
        SELECT
            o.order_id,
            TO_CHAR(o.order_date,       'DD Mon YYYY HH24:MI') AS order_date,
            TO_CHAR(o.expected_delivery,'DD Mon YYYY HH24:MI') AS expected_delivery,
            o.delivery_address,
            o.delivery_charge,
            o.special_note,

            s.sale_id,
            TO_CHAR(s.sale_date,'DD Mon YYYY HH24:MI') AS sale_date,
            s.order_type,
            s.subtotal,
            s.discount_amt,
            s.tax_amt,
            s.total_amt,
            s.payment_status,

            b.branch_name,

            COALESCE(c.cust_name, 'Walk-in') AS customer,
            c.phone,
            c.membership_type,

            e.emp_name AS cashier,

            py.method   AS payment_method,
            py.status   AS payment_status_detailed,

            dl.delivery_status  AS delivery_status,
            re.emp_name         AS rider_name

        FROM   online_order o

        JOIN   branch   b ON o.branch_id = b.branch_id
        JOIN   employee e ON o.branch_id = b.branch_id

        LEFT JOIN sale     s  ON o.sale_id = s.sale_id
        LEFT JOIN customer c  ON o.cust_id = c.cust_id
        LEFT JOIN employee ec ON s.emp_id  = ec.emp_id
        LEFT JOIN payment  py ON s.sale_id = py.sale_id
        LEFT JOIN delivery dl ON o.order_id = dl.order_id
        LEFT JOIN employee re ON dl.rider_id = re.emp_id

        WHERE  o.order_id = %s
          AND  o.branch_id = %s
    """, (order_id, branch_id))

    if not order:
        return JSONResponse(
            {"error": "Order not found for your branch"},
            status_code=404,
        )

    row = order[0]

    # Sale may not exist yet (e.g. order just placed, not yet invoiced).
    if not row.get("sale_id"):
        return JSONResponse(
            {"error": "No invoice generated yet for this order"},
            status_code=409,
        )

    sale_id = row["sale_id"]

    # ── Items — reuse the same JOIN shape as the cashier endpoint ───
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
        FROM   sale_item si
        JOIN   product   p  ON si.product_id   = p.product_id
        LEFT JOIN discount d ON si.discount_id = d.discount_id
        WHERE  si.sale_id = %s
        ORDER  BY p.product_name
    """, (sale_id,))

    formatted_items = []
    for item in items:
        disc_display = ""
        qty            = float(item["quantity"])
        line_total     = float(item["line_total"])
        unit_price_now = float(item["unit_price"])

        has_discount = bool(item["discount_name"]) and item["discount_value"] is not None
        disc_value   = float(item["discount_value"]) if has_discount else 0.0

        # Mirror the cashier endpoint's heuristic:
        #   • IN_STORE rows have unit_price = ORIGINAL price, line_total = discounted line
        #   • ONLINE  rows have unit_price = POST-DISCOUNT price, line_total = disc unit × qty
        # When qty × unit_price is greater than line_total, the stored unit
        # price is already the original — trust it.  When they're equal
        # within rounding, unit_price is the discounted unit and we recover
        # the original via the discount rate.
        pre_line = round(qty * unit_price_now, 2)
        unit_already_original = round(pre_line - line_total, 2) > 0.005

        if has_discount and not unit_already_original and disc_value < 100:
            if item["discount_type"] == "PERCENT":
                original_unit = unit_price_now / (1 - disc_value / 100)
            else:
                original_unit = unit_price_now + disc_value
            original_line = original_unit * qty
        else:
            original_unit = unit_price_now
            original_line = pre_line

        if has_discount:
            if item["discount_type"] == "PERCENT":
                disc_display = f"{disc_value:g}%"
            else:
                disc_display = f"৳{disc_value:.2f}"

        formatted_items.append({
            "product_name":    item["product_name"],
            "unit":            item["unit"],
            "quantity":        qty,
            "unit_price":      round(original_unit, 2),  # pre-discount price
            "line_total":      round(original_line, 2),  # pre-discount line total
            "discount_name":   item["discount_name"],
            "discount_value":  float(item["discount_value"]) if item["discount_value"] is not None else None,
            "discount_type":   item["discount_type"],
            "discounted_unit": unit_price_now,
            "discounted_line": line_total,
            "disc_display":    disc_display,
        })

    # ── Live totals from the items table (ignores stale sale.* fields) ─
    # sale.subtotal/discount_amt/tax_amt can drift from sale_item when a
    # customer removes a line post-checkout.  Recompute everything from
    # the items we just rendered so the receipt matches row-by-row.
    delivery_charge = float(row["delivery_charge"] or 0)
    live_subtotal   = round(sum(i["line_total"] for i in formatted_items), 2)
    live_discount   = round(sum(
        (i["line_total"] - i["discounted_line"]) for i in formatted_items
        if i.get("discount_name")
    ), 2)
    # Tax rate inferred from the stored header so we honour the same 4 %
    # rule the checkout used (and don't hard-code a number here).
    tax_base_hdr = float(row["subtotal"] or 0) - float(row["discount_amt"] or 0)
    tax_rate = (float(row["tax_amt"] or 0) / tax_base_hdr) if tax_base_hdr > 0 else 0.04
    live_tax       = round((live_subtotal - live_discount) * tax_rate, 2)
    # Grand total EXCLUDES delivery_charge — that field on online_order is
    # only a routing/fee record for the rider flow.  It must NEVER be folded
    # into the customer's bill, otherwise assigning a rider (or any later
    # update that touches online_order.delivery_charge) silently re-prices
    # the already-issued receipt.  The UI may still render `delivery_charge`
    # as a separate line, but `total_amt` stays Subtotal − Discount + Tax.
    live_total     = round(live_subtotal - live_discount + live_tax, 2)

    # ── Loyalty points earned (1 pt per 10 BDT of the LIVE grand total)
    loyalty_earned = int(live_total // 10)

    return JSONResponse({
        # ── Receipt identity (use order_id for cashier = sale_id parity)
        "sale_id":        row["sale_id"],
        "sale_date":      row["sale_date"],
        "branch_name":    row["branch_name"],
        "customer":       row["customer"],
        "membership":     row["membership_type"],
        "cashier":        row["cashier"],
        "order_type":     row["order_type"],
        "payment_status": row["payment_status"],
        "payment_method": row["payment_method"],

        # ── Totals (live-recomputed; delivery_charge added into total_amt)
        "subtotal":      live_subtotal,
        "discount_amt":  live_discount,
        "tax_amt":       live_tax,
        "total_amt":     live_total,
        "loyalty_earned": loyalty_earned,

        # ── Online-order specific extras (UI may or may not render these)
        "order_id":           row["order_id"],
        "expected_delivery":  row["expected_delivery"],
        "delivery_address":   row["delivery_address"],
        "delivery_charge":    delivery_charge,
        "delivery_status":    row["delivery_status"],
        "rider_name":         row["rider_name"],
        "special_note":       row["special_note"],

        "items": formatted_items,
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
            "position": session.get("position"),
            **_get_branch_info(session.get("branch_id"))
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
        **_get_branch_info(branch_id)
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
    success  = request.query_params.get("success")
    error    = request.query_params.get("error")
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
        "success":      success,
        "error":        error,
        **_get_branch_info(session.get("branch_id"))
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
            "/employee/delivery_rider/dashboard?error=Invalid+status+transition",
            status_code=302
        )

    existing = query(
        "SELECT delivery_status FROM delivery WHERE delivery_id = %s AND rider_id = %s",
        (delivery_id, rider_id)
    )
    if not existing:
        return RedirectResponse(
            "/employee/delivery_rider/dashboard?error=Delivery+not+found+or+not+assigned+to+you",
            status_code=302
        )

    current = existing[0]["delivery_status"]
    TERMINAL = {"DELIVERED", "FAILED"}
    if current in TERMINAL:
        return RedirectResponse(
            "/employee/delivery_rider/dashboard?error=Delivery+is+already+finalised",
            status_code=302
        )

    ts_col = {
        "PICKED_UP":  "picked_up_at  = CURRENT_TIMESTAMP,",
        "ON_THE_WAY": "",
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

    if new_status == "PICKED_UP":
        execute("""
            UPDATE online_order oo
            SET    order_status = 'OUT_FOR_DELIVERY'
            FROM   delivery d
            WHERE  d.delivery_id = %s
              AND  d.order_id    = oo.order_id
        """, (delivery_id,))

    if new_status == "DELIVERED":
        execute("""
            UPDATE online_order oo
            SET    order_status   = 'DELIVERED',
                   actual_delivery = CURRENT_TIMESTAMP
            FROM   delivery d
            WHERE  d.delivery_id = %s
              AND  d.order_id    = oo.order_id
        """, (delivery_id,))

        # ── Finalize billing now that delivery is confirmed ─────────────
        info = query("""
            SELECT oo.cust_id, oo.delivery_charge,
                   s.sale_id, s.total_amt, s.payment_status
            FROM   delivery d
            JOIN   online_order oo ON d.order_id = oo.order_id
            JOIN   sale s          ON oo.sale_id  = s.sale_id
            WHERE  d.delivery_id = %s
        """, (delivery_id,))

        if info:
            info         = info[0]
            sale_id      = info["sale_id"]
            cust_id      = info["cust_id"]
            total_amt    = float(info["total_amt"] or 0)
            delivery_fee = float(info["delivery_charge"] or 0)

            # COD: only becomes PAID once cash is actually collected
            if info["payment_status"] == "PENDING":
                max_pay = query("""
                    SELECT MAX(CAST(SUBSTRING(payment_id FROM 5) AS INTEGER)) AS mx
                    FROM   payment WHERE payment_id ~ '^PAY-[0-9]+$'
                """, ())
                pay_id = f"PAY-{(max_pay[0]['mx'] or 0) + 1:04d}"
                execute("""
                    INSERT INTO payment (payment_id, sale_id, amount, method, status)
                    VALUES (%s, %s, %s, 'CASH', 'SUCCESS')
                """, (pay_id, sale_id, total_amt))
                execute("UPDATE sale SET payment_status = 'PAID' WHERE sale_id = %s", (sale_id,))

                points_earned = int(total_amt // 10)
                if points_earned > 0:
                    execute("""
                        UPDATE customer SET loyalty_points = loyalty_points + %s
                        WHERE cust_id = %s
                    """, (points_earned, cust_id))

            # Delivery fee: always cash-collected by the rider, even on
            # prepaid online orders
            if delivery_fee > 0:
                max_pay2 = query("""
                    SELECT MAX(CAST(SUBSTRING(payment_id FROM 5) AS INTEGER)) AS mx
                    FROM   payment WHERE payment_id ~ '^PAY-[0-9]+$'
                """, ())
                pay_id2 = f"PAY-{(max_pay2[0]['mx'] or 0) + 1:04d}"
                execute("""
                    INSERT INTO payment (payment_id, sale_id, amount, method, status, reference_no)
                    VALUES (%s, %s, %s, 'CASH', 'SUCCESS', %s)
                """, (pay_id2, sale_id, delivery_fee, f"Delivery fee - {delivery_id}"))

    elif new_status == "FAILED":
        # Need order_id — this route only receives delivery_id
        order_row = query("SELECT order_id FROM delivery WHERE delivery_id = %s", (delivery_id,))
        order_id = order_row[0]["order_id"] if order_row else None

        execute("""
            UPDATE online_order oo
            SET    order_status = 'CANCELLED'
            FROM   delivery d
            WHERE  d.delivery_id = %s
              AND  d.order_id    = oo.order_id
        """, (delivery_id,))

        if order_id:
            _cancel_and_refund(order_id)

    # ── Tell the customer the delivery status changed ────────────────
    # We need cust_id + order_id.  Fall back to a fresh join if `info`
    # was never populated (e.g. only PICKED_UP / ON_THE_WAY / FAILED).
    try:
        if new_status in ("PICKED_UP", "ON_THE_WAY", "DELIVERED", "FAILED"):
            ctx = info if new_status == "DELIVERED" and info else None
            if ctx is None:
                row = query("""
                    SELECT oo.cust_id, d.order_id
                    FROM   delivery d
                    JOIN   online_order oo ON d.order_id = oo.order_id
                    WHERE  d.delivery_id  = %s
                """, (delivery_id,))
                ctx = row[0] if row else {}

            cust_id  = ctx.get("cust_id")
            order_id = ctx.get("order_id")
            if cust_id and order_id:
                if new_status == "PICKED_UP":
                    notify_customer(
                        cust_id, "ORDER_OUT_FOR_DELIVERY",
                        "Out for delivery",
                        f"Your order {order_id} has been picked up and is on its way.",
                        link_url="/customer/dashboard",
                        ref_table="online_order", ref_id=order_id,
                    )
                elif new_status == "ON_THE_WAY":
                    notify_customer(
                        cust_id, "ORDER_OUT_FOR_DELIVERY",
                        "Out for delivery",
                        f"Your order {order_id} is on the way to you.",
                        link_url="/customer/dashboard",
                        ref_table="online_order", ref_id=order_id,
                    )
                elif new_status == "DELIVERED":
                    notify_customer(
                        cust_id, "ORDER_DELIVERED",
                        "Order delivered",
                        f"Your order {order_id} has been delivered. Enjoy!",
                        link_url="/customer/dashboard",
                        ref_table="online_order", ref_id=order_id,
                    )
                elif new_status == "FAILED":
                    notify_customer(
                        cust_id, "ORDER_CANCELLED",
                        "Delivery failed",
                        f"We couldn't deliver your order {order_id}. "
                        "A refund will be processed shortly.",
                        link_url="/customer/dashboard",
                        ref_table="online_order", ref_id=order_id,
                    )
    except Exception as _err:
        print(f"[notify] rider status customer notify failed: {_err}")

    return RedirectResponse(
        f"/employee/delivery_rider/dashboard?success=Delivery+{delivery_id}+updated+to+{new_status.replace('_','+')}",
        status_code=302
    )


# ══════════════════════════════════════════════════════════════════════════════
#  ADD STAFF — POST /employee/branch/staff/add
#  Paste this route into employee.py, right after the employees_page GET route.
#
#  Rules:
#  • emp_id is auto-generated (numeric-only MAX, format E-XXXXX)
#  • branch_id is taken from the session (the manager's own branch)
#  • is_active defaults to 'N' — admin activates later
#  • Only CASHIER, SALES_STAFF, DELIVERY_RIDER positions are allowed
# ══════════════════════════════════════════════════════════════════════════════

@employee_router.post("/branch/staff/add")
def add_staff(
    request:           Request,
    emp_name:          str   = Form(...),
    gender:            str   = Form(...),
    position:          str   = Form(...),
    dept_id:           str   = Form(""),
    email:             str   = Form(""),
    phone:             str   = Form(...),
    salary:            float = Form(...),
    hire_date:         str   = Form(...),
    password:          str   = Form(...),
    confirm_password:  str   = Form(...),
    session=Depends(require_branch_manager),
):
    branch_id = session.get("branch_id")

    # ── Guard: only branch-level positions allowed ────────────────────────────
    ALLOWED_POSITIONS = {"CASHIER", "SALES_STAFF", "DELIVERY_RIDER"}
    if position not in ALLOWED_POSITIONS:
        return RedirectResponse(
            "/employee/branch/staff?error=Invalid+position+selected",
            status_code=302,
        )

    # ── Guard: password validation (matches create_manager) ───────────────────
    if len(password) < 6:
        return RedirectResponse(
            "/employee/branch/staff?error=Password+must+be+at+least+6+characters",
            status_code=302,
        )
    if password != confirm_password:
        return RedirectResponse(
            "/employee/branch/staff?error=Passwords+do+not+match",
            status_code=302,
        )

    # ── Guard: phone must be unique across employees AND app_user (EMPLOYEE) ──
    phone_clean = phone.strip()
    if query("SELECT 1 FROM employee WHERE phone = %s", (phone_clean,)):
        return RedirectResponse(
            "/employee/branch/staff?error=That+phone+number+is+already+registered",
            status_code=302,
        )
    if query("SELECT 1 FROM app_user WHERE phone = %s AND role = 'EMPLOYEE'", (phone_clean,)):
        return RedirectResponse(
            "/employee/branch/staff?error=That+phone+already+has+an+employee+login",
            status_code=302,
        )

    # ── Guard: email uniqueness (only if provided) ────────────────────────────
    clean_email = email.strip().lower() or None
    if clean_email:
        if query("SELECT 1 FROM employee WHERE email = %s", (clean_email,)):
            return RedirectResponse(
                "/employee/branch/staff?error=That+email+is+already+in+use",
                status_code=302,
            )

    # ── Guard: minimum salary (matches create_manager) ────────────────────────
    if salary < 10000:
        return RedirectResponse(
            "/employee/branch/staff?error=Salary+must+be+at+least+৳10,000",
            status_code=302,
        )

    # ── Auto-generate emp_id (numeric-only MAX to avoid format collisions) ────
    max_row = query("""
        SELECT MAX(CAST(SUBSTRING(emp_id FROM 3) AS INTEGER)) AS mx
        FROM   employee
        WHERE  emp_id ~ '^E-[0-9]+$'
    """, ())
    next_n = (max_row[0]["mx"] or 0) + 1
    emp_id = f"E-{next_n:05d}"

    # ── Auto-generate user_id (matches create_manager) ────────────────────────
    user_rows = query("""
        SELECT user_id FROM app_user ORDER BY user_id DESC LIMIT 1
    """, ())
    if not user_rows:
        user_id = "U-000001"
    else:
        last = user_rows[0]["user_id"]
        user_id = f"U-{int(last.split('-')[1]) + 1:06d}"
    pw_hash = _hash(password)

    # ── Insert employee (is_active = 'N' — admin activates later) ────────────
    execute("""
        INSERT INTO employee
            (emp_id, emp_name, email, phone,
             branch_id, dept_id, position,
             salary, hire_date, gender, is_active)
        VALUES (%s, %s, %s, %s,
                %s, %s, %s,
                %s, %s, %s, 'N')
    """, (
        emp_id,
        emp_name.strip(),
        clean_email,
        phone_clean,
        branch_id,
        dept_id.strip() or None,
        position,
        salary,
        hire_date,
        gender,
    ))

    # ── Create the matching app_user EMPLOYEE row (temp password) ─────────────
    execute("""
        INSERT INTO app_user
            (user_id, phone, password_hash, role, ref_id, is_active, created_at)
        VALUES (%s, %s, %s, 'EMPLOYEE', %s, 'Y', CURRENT_TIMESTAMP)
    """, (user_id, phone_clean, pw_hash, emp_id))

    # ── Notify admin: new employee needs review + activation ──────────────────
    manager_name = session.get("user_name") or "Branch Manager"
    try:
        notify_all_admins(
            "NEW_EMPLOYEE_PENDING",
            "New staff pending review",
            f"{emp_name.strip()} ({emp_id}) was added by {manager_name} "
            f"as {position.replace('_', ' ').title()} at branch {branch_id}. "
            f"Review and activate them to enable login.",
            link_url="/admin/dashboard/employees?pending=1",
            ref_table="employee",
            ref_id=emp_id,
        )
    except Exception:
        # Notifications must never break the staff-add flow
        pass

    return RedirectResponse(
        f"/employee/branch/staff?success=Staff+member+{emp_id}+added.+Temporary+password+set+for+login.",
        status_code=302,
    )

@employee_router.get("/notifications")
def list_notifications(session=Depends(require_employee)):
    rows = query("""
        SELECT notif_id, notif_type, title, message, link_url, is_read,
               TO_CHAR(created_at, 'DD Mon, HH12:MI AM') AS created_at
        FROM   notification
        WHERE  recipient_type = 'EMPLOYEE' AND recipient_id = %s
        ORDER  BY created_at DESC
        LIMIT  20
    """, (session["user_id"],))
    unread = sum(1 for r in rows if r["is_read"] == "N")
    return JSONResponse({"notifications": rows, "unread_count": unread})


@employee_router.post("/notifications/{notif_id}/read")
def mark_read(notif_id: str, session=Depends(require_employee)):
    execute("""
        UPDATE notification SET is_read='Y', read_at=CURRENT_TIMESTAMP
        WHERE  notif_id = %s AND recipient_type='EMPLOYEE' AND recipient_id = %s
    """, (notif_id, session["user_id"]))
    return JSONResponse({"ok": True})

    
def _cancel_and_refund(order_id: str):
    """Single source of truth for cancelling an online order — restocks
    inventory, reverses loyalty points and refunds payment if money was
    already collected, and closes out the sale. Idempotent."""
    row = query("""
        SELECT s.sale_id, s.cust_id, s.total_amt, s.payment_status
        FROM   online_order oo JOIN sale s ON oo.sale_id = s.sale_id
        WHERE  oo.order_id = %s
    """, (order_id,))
    if not row:
        return
    row = row[0]
    sale_id, cust_id = row["sale_id"], row["cust_id"]

    if row["payment_status"] == "CANCELLED":
        return  # already handled — don't double-refund or double-restock

    # ── Restock every item sold in this order ────────────────────────
    items = query("SELECT product_id, quantity FROM sale_item WHERE sale_id = %s", (sale_id,))
    for it in items:
        execute("""
            UPDATE branch_inventory bi
            SET    quantity = quantity + %s
            FROM   online_order oo
            WHERE  bi.product_id = %s AND bi.branch_id = oo.branch_id
              AND  oo.order_id = %s
        """, (it["quantity"], it["product_id"], order_id))

    # ── Refund + reverse points only if money was actually collected ──
    if row["payment_status"] == "PAID":
        execute("""
            UPDATE payment SET status = 'REFUNDED'
            WHERE sale_id = %s AND status = 'SUCCESS'
        """, (sale_id,))
        points_to_reverse = int(float(row["total_amt"] or 0) // 10)
        if points_to_reverse > 0 and cust_id:
            execute("""
                UPDATE customer
                SET loyalty_points = GREATEST(loyalty_points - %s, 0)
                WHERE cust_id = %s
            """, (points_to_reverse, cust_id))
    # PENDING (COD, never charged) needs no refund — nothing was collected.

    execute("UPDATE sale SET payment_status = 'CANCELLED' WHERE sale_id = %s", (sale_id,))