import os
from datetime import datetime, timezone, timedelta
from fastapi import FastAPI,APIRouter, Request, Form, HTTPException, Depends
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from action_logger import log_action
from auth import _hash, _verify
from branch_routes import branch_router
from database import query, execute
from customer import customer_router
from auth import (
    auth_router,
    require_admin,
    require_employee,
    require_customer,
    require_login,
)
from notifications import (
    notify_all_branch_managers,
    notify_branch_manager,
    notify_all_admins,
)


# ══════════════════════════════════════════════════════════════════════════════
#  ADMIN NOTIFICATIONS — context + helpers shared by every admin page
# ══════════════════════════════════════════════════════════════════════════════

def _fetch_admin_notifications(admin_id: str, limit: int = 10):
    """Return the most recent N notifications for the given admin (any admin
    can see them because they all share the same notification pool when an
    event is broadcast to all admins via notify_all_admins())."""
    rows = query("""
        SELECT notif_id, notif_type, title, message, link_url,
               is_read, ref_table, ref_id,
               TO_CHAR(created_at, 'DD Mon YYYY, HH12:MI AM') AS created_at
        FROM   notification
        WHERE  recipient_type = 'ADMIN'
          AND  (recipient_id = %s OR recipient_id IS NULL)
        ORDER  BY created_at DESC
        LIMIT  %s
    """, (admin_id, limit))
    return rows


def _pending_employee_count() -> int:
    """How many employee rows are waiting on admin activation."""
    row = query("""
        SELECT COUNT(*) AS n
        FROM   employee
        WHERE  is_active = 'N'
    """, ())
    return int(row[0]["n"]) if row else 0


def _admin_context(session: dict, **extra) -> dict:
    """Build the common admin template context (notifications + counters)."""
    admin_id = session.get("user_id") if session else None
    notifications = _fetch_admin_notifications(admin_id) if admin_id else []
    unread_count  = sum(1 for n in notifications if n.get("is_read") == "N")
    base = {
        "notifications":  notifications,
        "unread_count":   unread_count,
        "pending_staff":  _pending_employee_count(),
        "user_name":      session.get("user_name") if session else None,
        "role":           "ADMIN",
    }
    base.update(extra)
    return base

# Bangladesh is UTC+6 — apply it consistently so log timestamps match local time
BD_TZ = timezone(timedelta(hours=6))
def _to_bd(dt):
    """Convert an aware or naive datetime/date to BD-local and return formatted 'DD Mon YYYY HH24:MI'."""
    if dt is None:
        return None
    if isinstance(dt, datetime):
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(BD_TZ).strftime("%d %b %Y %H:%M")
    # Fallback: it's a date or something else — leave it untouched
    return str(dt)

admin_router = APIRouter(prefix="/admin", tags=["Admin"])
templates = Jinja2Templates(directory="templates")
templates.env.filters["bdtime"] = _to_bd


def _render(request: Request, template_name: str, session: dict, **extra):
    """Single point of admin template rendering. Always merges in
    notifications + pending_staff + user_name + role so child templates
    never need to worry about context plumbing."""
    return templates.TemplateResponse(
        request,
        template_name,
        _admin_context(session, **extra),
    )

# ══════════════════════════════════════════════════════════════════════════════
#  ADMIN DASHBOARD  (protected — ADMIN only)
# ══════════════════════════════════════════════════════════════════════════════

@admin_router.get("/dashboard", response_class=HTMLResponse)
def admin_dashboard(request: Request, session=Depends(require_admin)):

    stats = {
        "total_revenue": query("""
            SELECT COALESCE(SUM(total_amt),0) AS n
            FROM sale
            WHERE payment_status='PAID'
        """)[0]["n"],

        "total_orders": query("""
            SELECT COUNT(*) AS n
            FROM sale
        """)[0]["n"],

        "products": query("""
            SELECT COUNT(*) AS n
            FROM product
            WHERE is_active='Y'
        """)[0]["n"],

        "pending_orders": query("""
            SELECT COUNT(*) AS n
            FROM sale
            WHERE payment_status='PENDING'
        """)[0]["n"],

        "today_sales": query("""
            SELECT COUNT(*) AS n
            FROM sale
            WHERE DATE(sale_date)=CURRENT_DATE
        """)[0]["n"],

        "riders": query("""
            SELECT COUNT(*) AS n
            FROM employee
            WHERE position='DELIVERY_RIDER'
            AND is_active='Y'
        """)[0]["n"],
    }

    recent_sales = query("""
        SELECT s.sale_id,
               b.branch_name,
               COALESCE(c.cust_name,'Walk-in') AS customer,
               s.total_amt,
               s.payment_status
        FROM sale s
        JOIN branch b
            ON s.branch_id=b.branch_id
        LEFT JOIN customer c
            ON s.cust_id=c.cust_id
        ORDER BY s.sale_date DESC
        LIMIT 8
    """)

    branch_stats = query("""
        SELECT b.branch_name,
               COUNT(s.sale_id) AS sale_count,
               COALESCE(SUM(s.total_amt),0) AS revenue
        FROM branch b
        LEFT JOIN sale s
            ON b.branch_id=s.branch_id
            AND s.payment_status='PAID'
        GROUP BY b.branch_name
        ORDER BY revenue DESC
        LIMIT 5
    """)

    top_products = query("""
        SELECT p.product_name,
               c.cat_name,
               p.unit_price,
               COALESCE(SUM(si.quantity),0) AS times_sold
        FROM product p
        LEFT JOIN category c
            ON p.cat_id=c.cat_id
        LEFT JOIN sale_item si
            ON p.product_id=si.product_id
        GROUP BY p.product_name,
                 c.cat_name,
                 p.unit_price
        ORDER BY times_sold DESC
        LIMIT 5
    """)

    weekly = query("""
        SELECT TO_CHAR(DATE(sale_date),'Dy') AS day,
               COALESCE(SUM(total_amt),0) AS revenue
        FROM sale
        WHERE sale_date >= CURRENT_DATE - INTERVAL '6 day'
        GROUP BY DATE(sale_date)
        ORDER BY DATE(sale_date)
    """)

    chart_labels = [row["day"] for row in weekly]
    chart_data = [float(row["revenue"]) for row in weekly]

    return _render(
        request,
        "admin/index.html",
        session,
        stats=stats,
        recent_sales=recent_sales,
        branch_stats=branch_stats,
        top_products=top_products,
        chart_labels=chart_labels,
        chart_data=chart_data,
    )


# @admin_router.get("/dashboard/products", response_class=HTMLResponse)
# def admin_products_page(request: Request, session=Depends(require_admin)):
#     products = query("""
#         SELECT p.product_id, p.product_name, p.brand,
#                p.unit_price, p.unit, p.is_active,
#                c.cat_name, s.supplier_name
#         FROM   product p
#                LEFT JOIN category c  USING (cat_id)
#                LEFT JOIN supplier s  USING (supplier_id)
#         ORDER BY p.product_name
#     """)
#     return templates.TemplateResponse(request, "admin/products.html", {
#         "products":  products,
#         "user_name": session.get("user_name"),
#         "role":      session.get("role"),
#     })


@admin_router.get("/dashboard/customers", response_class=HTMLResponse)
def customers_page(request: Request, session=Depends(require_admin)):
    customers = query("""
        SELECT cust_id, cust_name, email, phone,
               gender, membership_type, loyalty_points,
               TO_CHAR(join_date, 'DD Mon YYYY') AS join_date
        FROM   customer
        ORDER BY cust_name
    """)
    return _render(request, "admin/customers.html", session, customers=customers)


@admin_router.get("/dashboard/employees", response_class=HTMLResponse)
def employees_page(
    request: Request,
    pending: str = "",
    session=Depends(require_admin),
):
    employees = query("""
        SELECT e.emp_id,
               e.emp_name,
               e.email,
               e.phone,
               e.position,
               e.salary,
               e.gender,
               e.is_active,
               e.branch_id,
               e.dept_id,
               b.branch_name,
               d.dept_name,
               TO_CHAR(e.hire_date, 'YYYY-MM-DD') AS hire_date
        FROM employee e
        LEFT JOIN branch b
            ON e.branch_id = b.branch_id
        LEFT JOIN department d
            ON e.dept_id = d.dept_id
        ORDER BY e.is_active ASC, e.emp_name ASC
    """)

    departments = query("""
        SELECT dept_id, dept_name
        FROM   department
        ORDER BY dept_name
    """)

    branches = query("""
        SELECT branch_id, branch_name
        FROM   branch
        WHERE  is_active = 'Y'
        ORDER BY branch_name
    """)

    # Pending = employees whose is_active is 'N'. ?pending=1 → only show those.
    pending_only = (pending == "1")
    pending_count = sum(1 for e in employees if e.get("is_active") == "N")
    if pending_only:
        employees = [e for e in employees if e.get("is_active") == "N"]

    return _render(
        request,
        "admin/employees.html",
        session,
        employees=employees,
        departments=departments,
        branches=branches,
        pending_only=pending_only,
        pending_count=pending_count,
    )


@admin_router.post("/dashboard/employees/{emp_id}/activate")
def activate_employee(
    request: Request,
    emp_id: str,
    session=Depends(require_admin),
):
    """Mark an inactive employee as active. Used by the Pending Review flow
    when a branch manager adds a new staff member and the admin approves."""
    exists = query("SELECT emp_id, emp_name, is_active FROM employee WHERE emp_id = %s", (emp_id,))
    if not exists:
        return RedirectResponse(
            "/admin/dashboard/employees?pending=1&error=Employee+not+found",
            status_code=302,
        )
    if exists[0]["is_active"] == "Y":
        return RedirectResponse(
            "/admin/dashboard/employees?error=Employee+already+active",
            status_code=302,
        )

    execute("""
        UPDATE employee
        SET    is_active = 'Y'
        WHERE  emp_id    = %s
    """, (emp_id,))

    # If they have an app_user row (typical), keep it active; otherwise skip.
    execute("""
        UPDATE app_user
        SET    is_active = 'Y'
        WHERE  role = 'EMPLOYEE' AND ref_id = %s
    """, (emp_id,))

    # Mark related admin notifications as read so the bell stops nagging.
    execute("""
        UPDATE notification
        SET    is_read = 'Y', read_at = CURRENT_TIMESTAMP
        WHERE  recipient_type = 'ADMIN'
          AND  ref_table     = 'employee'
          AND  ref_id        = %s
          AND  is_read       = 'N'
    """, (emp_id,))

    log_action(
        session, "UPDATE", "employee", emp_id,
        f"Activated employee {exists[0]['emp_name']} ({emp_id})",
        old_values={"is_active": "N"},
        new_values={"is_active": "Y"},
        request=request,
    )

    return RedirectResponse(
        f"/admin/dashboard/employees?success=Employee+{emp_id}+({exists[0]['emp_name']})+activated",
        status_code=302,
    )


@admin_router.post("/dashboard/employees/{emp_id}/deactivate")
def deactivate_employee(
    request: Request,
    emp_id: str,
    session=Depends(require_admin),
):
    """Reverse of activate_employee — soft-disable login."""
    exists = query("SELECT emp_id, emp_name, is_active FROM employee WHERE emp_id = %s", (emp_id,))
    if not exists:
        return RedirectResponse(
            "/admin/dashboard/employees?error=Employee+not+found",
            status_code=302,
        )
    if exists[0]["is_active"] == "N":
        return RedirectResponse(
            "/admin/dashboard/employees?error=Employee+already+inactive",
            status_code=302,
        )

    execute("UPDATE employee SET is_active = 'N' WHERE emp_id = %s", (emp_id,))
    execute("""
        UPDATE app_user
        SET    is_active = 'N'
        WHERE  role = 'EMPLOYEE' AND ref_id = %s
    """, (emp_id,))

    log_action(
        session, "UPDATE", "employee", emp_id,
        f"Deactivated employee {exists[0]['emp_name']} ({emp_id})",
        old_values={"is_active": "Y"},
        new_values={"is_active": "N"},
        request=request,
    )

    return RedirectResponse(
        f"/admin/dashboard/employees?success=Employee+{emp_id}+deactivated",
        status_code=302,
    )


@admin_router.post("/dashboard/employees/{emp_id}/edit")
def edit_employee(
    request:    Request,
    emp_id:     str,
    emp_name:   str   = Form(...),
    email:      str   = Form(""),
    phone:      str   = Form(""),
    gender:     str   = Form(...),
    position:   str   = Form(...),
    branch_id:  str   = Form(""),
    dept_id:    str   = Form(""),
    salary:     float = Form(...),
    hire_date:  str   = Form(...),
    is_active:  str   = Form(...),
    session=Depends(require_admin),
):
    # Validate salary
    if salary < 10000:
        return RedirectResponse(
            f"/admin/dashboard/employees?error=Salary+must+be+at+least+৳10,000",
            status_code=302,
        )

    # Validate email format if provided
    email_val = email.strip() if email and email.strip() else None
    if email_val and ("@" not in email_val or "." not in email_val):
        return RedirectResponse(
            f"/admin/dashboard/employees?error=Invalid+email+format",
            status_code=302,
        )

    # Validate position
    valid_positions = {"BRANCH_MANAGER", "CASHIER", "SALES_STAFF", "DELIVERY_RIDER"}
    if position not in valid_positions:
        return RedirectResponse(
            f"/admin/dashboard/employees?error=Invalid+position",
            status_code=302,
        )

    # Check for duplicate email (other employees)
    if email_val:
        dup = query("""
            SELECT 1
            FROM   employee
            WHERE  email = %s
              AND  emp_id <> %s
        """, (email_val, emp_id))
        if dup:
            return RedirectResponse(
                f"/admin/dashboard/employees?error=Email+already+used+by+another+employee",
                status_code=302,
            )

    dept_val = dept_id.strip() if dept_id and dept_id.strip() else None

    # Look up the current row BEFORE writing so we can compare old vs new
    current = query("""
        SELECT position, branch_id
        FROM   employee
        WHERE  emp_id = %s
    """, (emp_id,))
    if not current:
        return RedirectResponse(
            f"/admin/dashboard/employees?error=Employee+not+found",
            status_code=302,
        )
    old_pos    = current[0]["position"]
    old_branch = current[0]["branch_id"]


    # ── Decide branch_id for the UPDATE based on the new position ────────────
    # Rule 1: promoting TO branch_manager → employee.branch_id must be cleared,
    #         manager assignment is handled on the Manage Branches page.
    if position == "BRANCH_MANAGER":
        branch_val = None
    else:
        branch_val = branch_id.strip() if branch_id and branch_id.strip() else None

        # Validate branch_id if provided
        if branch_val:
            exists = query("""
                SELECT 1 FROM branch WHERE branch_id = %s
            """, (branch_val,))
            if not exists:
                return RedirectResponse(
                    f"/admin/dashboard/employees?error=Invalid+branch+selected",
                    status_code=302,
                )

    # Update employee record
    execute("""
        UPDATE employee
        SET    emp_name  = %s,
               email     = %s,
               phone     = %s,
               gender    = %s,
               position  = %s,
               branch_id = %s,
               dept_id   = %s,
               salary    = %s,
               hire_date = %s,
               is_active = %s
        WHERE  emp_id    = %s
    """, (
        emp_name.strip(),
        email_val,
        phone.strip() if phone and phone.strip() else None,
        gender,
        position,
        branch_val,
        dept_val,
        salary,
        hire_date,
        is_active,
        emp_id,
    ))

    # ── branch_manager housekeeping + redirect message ──────────────────────
    promote_to_bm    = (old_pos != "BRANCH_MANAGER" and position == "BRANCH_MANAGER")
    demote_from_bm   = (old_pos == "BRANCH_MANAGER" and position != "BRANCH_MANAGER")

    if promote_to_bm or demote_from_bm or old_branch != branch_val:
        # Any of these situations means the previous manager row is stale
        execute("""
            DELETE FROM branch_manager WHERE emp_id = %s
        """, (emp_id,))

    log_action(
    session, "UPDATE", "employee", emp_id,
    f"Updated employee {emp_id} ({emp_name})",
    old_values={"position": old_pos, "branch_id": old_branch},
    new_values={"position": position, "branch_id": branch_val},
    request=request,
)

    if promote_to_bm:
        return RedirectResponse(
            f"/admin/dashboard/employees?"
            f"success=Promoted+to+Branch+Manager.+employee.branch_id+cleared.+"
            f"Open+Manage+Branches+to+assign+this+employee+as+a+branch+manager.",
            status_code=302,
        )

    if demote_from_bm:
        return RedirectResponse(
            f"/admin/dashboard/employees?"
            f"success=Demoted+from+Branch+Manager.+Branch+now+shows+Unassigned+"
            f"manager+until+you+assign+a+new+one+via+Manage+Branches.",
            status_code=302,
        )

    return RedirectResponse(
        f"/admin/dashboard/employees?success=Employee+{emp_id}+updated+successfully",
        status_code=302,
    )


@admin_router.get("/dashboard/branches", response_class=HTMLResponse)
def branches_page(request: Request, session=Depends(require_login)):
    branches = query("""
        SELECT b.branch_id, b.branch_name, c.city_name,
               b.address, b.phone, b.open_time, b.close_time,
               b.is_active, e.emp_name AS manager_name
        FROM   branch b
               JOIN city c ON b.city_id = c.city_id
               LEFT JOIN branch_manager bm USING (branch_id)
               LEFT JOIN employee e ON bm.emp_id = e.emp_id
        ORDER BY b.branch_id
    """)
    return _render(request, "admin/branches.html", session, branches=branches)


@admin_router.get("/dashboard/discounts", response_class=HTMLResponse)
def discounts_page(request: Request, session=Depends(require_admin)):

    discounts = query("""
        SELECT
            d.discount_id,
            d.discount_name,
            d.discount_type,
            d.discount_value,
            d.product_id,
            d.cat_id,
            p.product_name,
            c.cat_name,
            TO_CHAR(d.start_date, 'DD Mon YYYY')  AS start_date,
            TO_CHAR(d.end_date,   'DD Mon YYYY')  AS end_date,
            TO_CHAR(d.start_date, 'YYYY-MM-DD')   AS start_date_raw,
            TO_CHAR(d.end_date,   'YYYY-MM-DD')   AS end_date_raw,
            CASE
                WHEN CURRENT_DATE BETWEEN d.start_date AND d.end_date THEN 'ACTIVE'
                WHEN CURRENT_DATE < d.start_date                      THEN 'UPCOMING'
                ELSE 'EXPIRED'
            END AS status
        FROM discount d
        LEFT JOIN product  p ON d.product_id = p.product_id
        LEFT JOIN category c ON d.cat_id     = c.cat_id
        ORDER BY d.start_date DESC
    """)

    categories = query("""
        SELECT cat_id, cat_name FROM category ORDER BY cat_name
    """)

    products = query("""
        SELECT product_id, product_name, cat_id
        FROM   product
        WHERE  is_active = 'Y'
        ORDER BY product_name
    """)

    # Generate next discount ID in DIS-XXX format
    last = query("""
        SELECT discount_id FROM discount ORDER BY discount_id DESC LIMIT 1
    """)
    if last:
        last_num = int(last[0]["discount_id"].split("-")[1])
        next_discount_id = f"DIS-{last_num + 1:03d}"
    else:
        next_discount_id = "DIS-001"

    return _render(
        request,
        "admin/discounts.html",
        session,
        discounts=discounts,
        categories=categories,
        products=products,
        next_discount_id=next_discount_id,
    )

@admin_router.post("/dashboard/discounts/add")
def add_discount(
    request:        Request,
    discount_id:    str   = Form(...),
    discount_name:  str   = Form(...),
    discount_type:  str   = Form(...),
    discount_value: float = Form(...),
    product_id:     str   = Form(""),
    cat_id_scope:   str   = Form(...),
    start_date:     str   = Form(...),
    end_date:       str   = Form(...),
    session=Depends(require_admin),
):
    pid = product_id.strip() if product_id and product_id.strip() else None
    cat = cat_id_scope.strip() if cat_id_scope and cat_id_scope.strip() else None
 
    if pid:
        final_pid = pid
        final_cat = cat
    else:
        final_pid = None
        final_cat = cat
 
    if not final_pid and not final_cat:
        return RedirectResponse(
            "/admin/dashboard/discounts?error=Please+select+at+least+a+category",
            status_code=302
        )
 
    execute("""
        INSERT INTO discount
            (discount_id, discount_name, discount_type, discount_value,
             product_id, cat_id, start_date, end_date)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        discount_id, discount_name.strip(), discount_type, discount_value,
        final_pid, final_cat, start_date, end_date,
    ))
 
    return RedirectResponse("/admin/dashboard/discounts?success=Discount+created", status_code=302)


@admin_router.post("/dashboard/discounts/modify")
def modify_discount(
    request:        Request,
    discount_id:    str   = Form(...),
    discount_name:  str   = Form(...),
    discount_type:  str   = Form(...),
    discount_value: float = Form(...),
    start_date:     str   = Form(...),
    end_date:       str   = Form(...),
    session=Depends(require_admin),
):
    execute("""
        UPDATE discount
        SET discount_name  = %s,
            discount_type  = %s,
            discount_value = %s,
            start_date     = %s,
            end_date       = %s
        WHERE discount_id = %s
    """, (
        discount_name.strip(),
        discount_type,
        discount_value,
        start_date,
        end_date,
        discount_id,
    ))

    return RedirectResponse("/admin/dashboard/discounts?success=Discount+updated", status_code=302)


@admin_router.post("/dashboard/discounts/delete")
def delete_discount(
    request:    Request,
    discount_id: str = Form(...),
    confirm_id:  str = Form(...),
    session=Depends(require_admin),
):
    if discount_id.strip() != confirm_id.strip():
        return RedirectResponse("/admin/dashboard/discounts?error=ID+mismatch", status_code=302)

    # execute("DELETE FROM discount WHERE discount_id = %s", (discount_id,))

    old_row = query("SELECT * FROM discount WHERE discount_id = %s", (discount_id,))
    execute("DELETE FROM discount WHERE discount_id = %s", (discount_id,))
    log_action(
        session, "DELETE", "discount", discount_id,
        f"Deleted discount {discount_id}",
        old_values=old_row[0] if old_row else None,
        request=request,
    )

    return RedirectResponse("/admin/dashboard/discounts?success=Discount+deleted", status_code=302)


@admin_router.get("/dashboard/sales", response_class=HTMLResponse)
def admin_sales(
    request: Request,
    session=Depends(require_admin)
):

    sales = query("""
        SELECT
            s.sale_id,
            TO_CHAR(s.sale_date,'DD Mon YYYY HH24:MI') AS sale_date,
            s.order_type,
            s.subtotal,
            s.discount_amt,
            s.total_amt,
            s.payment_status,
            b.branch_name,
            e.emp_name,
            COALESCE(c.cust_name, 'Walk-in') AS customer
        FROM sale s
        JOIN branch b
            ON s.branch_id = b.branch_id
        JOIN employee e
            ON s.emp_id = e.emp_id
        LEFT JOIN customer c
            ON s.cust_id = c.cust_id
        ORDER BY s.sale_date DESC
    """)

    return _render(
        request,
        "admin/sales.html",
        session,
        sales=sales,
    )


@admin_router.get("/dashboard/inventory", response_class=HTMLResponse)
def admin_inventory(request: Request, session=Depends(require_admin)):

    inventory = query("""
        SELECT bi.inv_id,
               b.branch_name,
               p.product_name,
               bi.quantity,
               bi.reorder_level,
               bi.shelf_location,
               TO_CHAR(bi.last_restocked, 'DD Mon YYYY') AS last_restocked,
               CASE
                   WHEN bi.quantity <= bi.reorder_level
                   THEN 'LOW'
                   ELSE 'OK'
               END AS stock_status
        FROM branch_inventory bi
        JOIN branch b USING(branch_id)
        JOIN product p USING(product_id)
        ORDER BY b.branch_name, p.product_name
    """)

    branches = query("""
        SELECT branch_id, branch_name
        FROM branch
        ORDER BY branch_name
    """)

    return _render(
        request,
        "admin/inventory.html",
        session,
        inventory=inventory,
        branches=branches,
    )


@admin_router.get("/dashboard/profile", response_class=HTMLResponse)
def admin_profile(
    request: Request,
    session=Depends(require_admin)
):
    admin = query("""
        SELECT
            admin_id,
            admin_name,
            email,
            is_active,
            TO_CHAR(created_at,'DD Mon YYYY HH24:MI') AS created_at
        FROM admin_account
        WHERE admin_id = %s
    """, (session["user_id"],))

    if not admin:
        raise HTTPException(status_code=404, detail="Admin not found")

    return _render(
        request,
        "admin/profile.html",
        session,
        admin=admin[0],
    )

@admin_router.post("/dashboard/profile/update")
def update_admin_profile(
    request: Request,
    admin_name: str = Form(...),
    email: str = Form(...),
    session=Depends(require_admin)
):
    admin_id = session["user_id"]

    existing = query("""
        SELECT 1
        FROM admin_account
        WHERE email = %s
        AND admin_id <> %s
    """, (email.strip(), admin_id))

    if existing:
        return RedirectResponse(
            "/admin/dashboard/profile?error=Email already exists",
            status_code=302
        )

    execute("""
        UPDATE admin_account
        SET admin_name = %s,
            email = %s
        WHERE admin_id = %s
    """, (
        admin_name.strip(),
        email.strip().lower(),
        admin_id
    ))

    request.session["user_name"] = admin_name.strip()

    return RedirectResponse(
        "/admin/dashboard/profile?success=Profile updated successfully",
        status_code=302
    )

@admin_router.post("/dashboard/profile/password")
def change_admin_password(
    request: Request,
    current_password: str = Form(...),
    new_password: str = Form(...),
    confirm_password: str = Form(...),
    session=Depends(require_admin)
):
    admin_id = session["user_id"]

    admin = query("""
        SELECT password_hash
        FROM admin_account
        WHERE admin_id = %s
    """, (admin_id,))

    if not admin:
        raise HTTPException(status_code=404)

    if not _verify(current_password, admin[0]["password_hash"]):
        return RedirectResponse(
            "/admin/dashboard/profile?error=Current password is incorrect",
            status_code=302
        )

    if new_password != confirm_password:
        return RedirectResponse(
            "/admin/dashboard/profile?error=Passwords do not match",
            status_code=302
        )

    if len(new_password) < 6:
        return RedirectResponse(
            "/admin/dashboard/profile?error=Password must be at least 6 characters",
            status_code=302
        )

    execute("""
        UPDATE admin_account
        SET password_hash = %s
        WHERE admin_id = %s
    """, (
        _hash(new_password),
        admin_id
    ))

    return RedirectResponse(
        "/admin/dashboard/profile?success=Password updated successfully",
        status_code=302
    )

@admin_router.get("/dashboard/branches/manage")
def manage_branches(
    request: Request,
    session=Depends(require_admin)
):
    branches = query("""
        SELECT b.branch_id, b.branch_name, c.city_name,
               b.address, b.phone, b.open_time, b.close_time,
               b.is_active, e.emp_name AS manager_name
        FROM branch b
        JOIN city c ON b.city_id = c.city_id
        LEFT JOIN branch_manager bm USING (branch_id)
        LEFT JOIN employee e ON bm.emp_id = e.emp_id
        ORDER BY b.branch_id
    """)

# ADD THIS — branch managers not assigned to any branch
    unassigned_managers = query("""
        SELECT emp_id, emp_name, branch_id
        FROM   employee
        WHERE  position = 'BRANCH_MANAGER'
          AND  is_active = 'Y'
          AND  emp_id NOT IN (SELECT emp_id FROM branch_manager)
        ORDER BY emp_name
    """)
   
    departments = query("SELECT dept_id, dept_name FROM department ORDER BY dept_name")

    cities = query("SELECT city_id, city_name, division FROM city ORDER BY city_name")
    return _render(
        request,
        "admin/manage_branches.html",
        session,
        branches=branches,
        unassigned_managers=unassigned_managers,
        cities=cities,
        departments=departments,
    )

@admin_router.get("/dashboard/suppliers")
def suppliers_page(
    request: Request,
    session=Depends(require_admin)
):

    suppliers = query("""
        SELECT *
        FROM supplier
        ORDER BY supplier_name
    """)

    return _render(
        request,
        "admin/suppliers.html",
        session,
        suppliers=suppliers,
    )

# ════════════════════════════════════════════════════════════════════════════
#  PRODUCTS — replace the existing admin_products_page() with this version,
#  and add the two new POST routes below it. Everything else in admin.py
#  (imports, admin_router, etc.) stays exactly as you already have it.
# ════════════════════════════════════════════════════════════════════════════

@admin_router.get("/dashboard/products", response_class=HTMLResponse)
def admin_products_page(
    request: Request,
    cat_id: str = "",          # ?cat_id=P-...  →  SQL-filtered category
    q:      str = "",          # ?q=milk        →  SQL-filtered search term
    sort:   str = "",          # ?sort=name_asc →  SQL-side ORDER BY
    session = Depends(require_admin),
):
    # ── Whitelist sort values (safe to plug into ORDER BY) ──────────────
    sort_map = {
        "name_asc":   "p.product_name ASC",
        "name_desc":  "p.product_name DESC",
        "price_asc":  "p.unit_price ASC, p.product_name ASC",
        "price_desc": "p.unit_price DESC, p.product_name ASC",
    }
    order_clause = sort_map.get(sort, "p.product_name ASC")

    # ── Build WHERE clauses dynamically ──────────────────────────────────
    where  = []
    params: list = []

    if cat_id == "__NONE__":
        where.append("p.cat_id IS NULL")
    elif cat_id:
        where.append("p.cat_id = %s")
        params.append(cat_id)

    if q:
        where.append("(LOWER(p.product_name) LIKE %s OR LOWER(COALESCE(p.brand,'')) LIKE %s)")
        like = f"%{q.lower()}%"
        params.extend([like, like])

    where_sql = ("WHERE " + " AND ".join(where)) if where else ""

    products = query(f"""
        SELECT p.product_id, p.product_name, p.brand,
               p.cat_id, p.supplier_id,
               p.unit_price, p.unit, p.is_active,
               c.cat_name, s.supplier_name
        FROM   product p
               LEFT JOIN category c  USING (cat_id)
               LEFT JOIN supplier s  USING (supplier_id)
        {where_sql}
        ORDER BY {order_clause}
    """, tuple(params))

    # Count per category (for the dropdown badges + "All" total)
    cat_counts_raw = query("""
        SELECT COALESCE(p.cat_id, '') AS cat_id,
               COUNT(*)              AS n
        FROM   product p
        GROUP BY COALESCE(p.cat_id, '')
    """)
    cat_counts = {row["cat_id"]: row["n"] for row in cat_counts_raw}
    total_all  = sum(cat_counts.values())

    categories = query("""
        SELECT cat_id, cat_name FROM category ORDER BY cat_name
    """)

    suppliers = query("""
        SELECT supplier_id, supplier_name FROM supplier ORDER BY supplier_name
    """)

    # Generate next product ID in P-XXXXX format
    last = query("""
        SELECT product_id FROM product ORDER BY product_id DESC LIMIT 1
    """)
    if last:
        last_num = int(last[0]["product_id"].split("-")[1])
        next_product_id = f"P-{last_num + 1:05d}"
    else:
        next_product_id = "P-00001"

    return _render(
        request,
        "admin/products.html",
        session,
        products=products,
        categories=categories,
        suppliers=suppliers,
        next_product_id=next_product_id,
        selected_cat=cat_id,
        search_term=q,
        sort_value=sort,
        cat_counts=cat_counts,
        total_all=total_all,
        clear_url=str(request.url_for("admin_products_page")),
    )


@admin_router.post("/dashboard/products/add")
def add_product(
    request:      Request,
    product_id:   str   = Form(...),
    product_name: str   = Form(...),
    brand:        str   = Form(""),
    cat_id:       str   = Form(""),
    supplier_id:  str   = Form(""),
    unit_price:   float = Form(...),
    unit:         str   = Form(...),
    session=Depends(require_admin),
):
    execute("""
        INSERT INTO product
            (product_id, product_name, brand, cat_id, supplier_id,
             unit_price, unit)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, (
        product_id,
        product_name.strip(),
        brand.strip() if brand and brand.strip() else None,
        cat_id.strip() if cat_id and cat_id.strip() else None,
        supplier_id.strip() if supplier_id and supplier_id.strip() else None,
        unit_price,
        unit.strip(),
    ))

    log_action(
    session, "CREATE", "product", product_id,
    f'Created product "{product_name}"',
    new_values={"cat_id": cat_id, "supplier_id": supplier_id, "unit_price": unit_price},
    request=request,
)
    
    notify_all_branch_managers(
        "NEW_PRODUCT",
        "New product added",
        f"{product_name} has been added by admin.",
        link_url="/employee/branch/products",
        ref_table="product", ref_id=product_id,
)

    return RedirectResponse(
        f"/admin/dashboard/products?success=Product+%22{product_name}%22+added+successfully",
        status_code=302,
    )


@admin_router.post("/dashboard/products/modify")
def modify_product(
    request:     Request,
    product_id:  str   = Form(...),
    cat_id:      str   = Form(""),
    supplier_id: str   = Form(""),
    unit_price:  float = Form(...),
    unit:        str   = Form(...),
    is_active:   str   = Form(...),
    session=Depends(require_admin),
):
    product_name_row = query(
        "SELECT product_name FROM product WHERE product_id = %s",
        (product_id,),
    )
    product_name = (
        product_name_row[0]["product_name"] if product_name_row else product_id
    )
    old_row = query("SELECT cat_id, supplier_id, unit_price, unit, is_active FROM product WHERE product_id = %s", (product_id,))
    execute("""
        UPDATE product
        SET cat_id      = %s,
            supplier_id = %s,
            unit_price  = %s,
            unit        = %s,
            is_active   = %s
        WHERE product_id = %s
    """, (
        cat_id.strip() if cat_id and cat_id.strip() else None,
        supplier_id.strip() if supplier_id and supplier_id.strip() else None,
        unit_price,
        unit.strip(),
        is_active,
        product_id,
    ))

    log_action(
    session, "UPDATE", "product", product_id,
    f'Updated product "{product_name}"',
    old_values=old_row[0] if old_row else None,
    new_values={"cat_id": cat_id, "supplier_id": supplier_id, "unit_price": unit_price, "unit": unit, "is_active": is_active},
    request=request,
)
    return RedirectResponse(
        f"/admin/dashboard/products?success=Product+%22{product_name}%22+updated+successfully",
        status_code=302,
    )

@admin_router.get("/dashboard/logs", response_class=HTMLResponse)
def action_logs_page(request: Request, session=Depends(require_admin)):
    logs = query("""
        SELECT log_id, actor_type, actor_name, action,
               table_name, record_id, description,
               old_values, new_values, created_at
        FROM action_log
        ORDER BY created_at DESC
        LIMIT 200
    """)
    # Format each row's created_at into BD-local time for display
    for row in logs:
        row["created_at"] = _to_bd(row.get("created_at"))
    return _render(request, "admin/logs.html", session, logs=logs)


# ══════════════════════════════════════════════════════════════════════════════
#  ADMIN NOTIFICATIONS — JSON endpoints used by the bell dropdown
# ══════════════════════════════════════════════════════════════════════════════

@admin_router.get("/notifications")
def admin_list_notifications(session=Depends(require_admin)):
    admin_id = session.get("user_id")
    rows = _fetch_admin_notifications(admin_id, limit=20)
    unread = sum(1 for r in rows if r.get("is_read") == "N")
    return JSONResponse({"notifications": rows, "unread_count": unread})


@admin_router.post("/notifications/{notif_id}/read")
def admin_mark_notification_read(notif_id: str, session=Depends(require_admin)):
    execute("""
        UPDATE notification
        SET    is_read  = 'Y',
               read_at  = CURRENT_TIMESTAMP
        WHERE  notif_id = %s
          AND  recipient_type = 'ADMIN'
    """, (notif_id,))
    return JSONResponse({"ok": True})


@admin_router.post("/notifications/read-all")
def admin_mark_all_notifications_read(session=Depends(require_admin)):
    admin_id = session.get("user_id")
    execute("""
        UPDATE notification
        SET    is_read = 'Y',
               read_at = CURRENT_TIMESTAMP
        WHERE  recipient_type = 'ADMIN'
          AND  is_read  = 'N'
          AND  (recipient_id = %s OR recipient_id IS NULL)
    """, (admin_id,))
    return JSONResponse({"ok": True})