"""
main.py  — SuperShop Bangladesh (updated to include auth)
==========================================================
Changes from your original:
  1. Added SessionMiddleware (required for request.session)
  2. Imported and registered auth_router
  3. Root route "/" redirects to login if not authenticated
  4. Admin dashboard route added as example protected route
  5. Employee/Customer dashboard stubs included
"""

import os
from fastapi import FastAPI, Request, Form, HTTPException, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from auth import _hash, _verify
from branch_routes import branch_router
from database import query, execute
from auth import (
    auth_router,
    require_admin,
    require_employee,
    require_customer,
    require_login,
)

# ── App setup ──────────────────────────────────────────────────────────────────
app = FastAPI(
    title="SuperShop Bangladesh",
    description="Multi-branch retail management system",
    version="1.0.0"
)

# ── Session middleware  (SECRET_KEY must be set in your .env) ──────────────────
app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SECRET_KEY", "change-this-in-production-32chars"),
    max_age=3600 * 8,       # session lasts 8 hours
    https_only=False,        # set True in production with HTTPS
)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# ── Register auth router  (/auth/login, /auth/logout, /auth/*/login) ──────────
app.include_router(auth_router)
app.include_router(branch_router)


# ══════════════════════════════════════════════════════════════════════════════
#  ROOT — redirect based on role
# ══════════════════════════════════════════════════════════════════════════════

# @app.get("/", response_class=HTMLResponse)
# def root(request: Request):
#     role = request.session.get("role")
#     if role == "ADMIN":
#         return RedirectResponse("/admin/dashboard")
#     if role == "EMPLOYEE":
#         return RedirectResponse("/employee/dashboard")
#     if role == "CUSTOMER":
#         return RedirectResponse("/customer/dashboard")
#     return RedirectResponse("/auth/login")
@app.get("/", response_class=HTMLResponse)
def storefront(request: Request):
    products = query("""
        SELECT product_id,
               product_name,
               brand,
               unit_price,
               unit
        FROM product
        WHERE is_active='Y'
        ORDER BY product_name
    """)

    return templates.TemplateResponse(
        request,
        "storefront.html",
        {
            "products": products,
            "logged_in": bool(request.session.get("role")),
            "role": request.session.get("role")
        }
    )

# ══════════════════════════════════════════════════════════════════════════════
#  ADMIN DASHBOARD  (protected — ADMIN only)
# ══════════════════════════════════════════════════════════════════════════════

@app.get("/admin/dashboard", response_class=HTMLResponse)
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

    return templates.TemplateResponse(
        request,
        "admin/index.html",
        {
            "stats": stats,
            "recent_sales": recent_sales,
            "branch_stats": branch_stats,
            "top_products": top_products,
            "chart_labels": chart_labels,
            "chart_data": chart_data,
            "user_name": session.get("user_name"),
            "role": "ADMIN",
        }
    )


# ══════════════════════════════════════════════════════════════════════════════
#  EMPLOYEE DASHBOARD  (protected — EMPLOYEE or ADMIN)
# ══════════════════════════════════════════════════════════════════════════════

@app.get("/employee/dashboard", response_class=HTMLResponse)
def employee_dashboard(request: Request, session=Depends(require_employee)):
    branch_id = session.get("branch_id")

    # Employee only sees their own branch data
    branch_sales = query("""
        SELECT s.sale_id,
               TO_CHAR(s.sale_date, 'DD Mon YYYY HH24:MI') AS sale_date,
               COALESCE(c.cust_name, 'Walk-in') AS customer,
               s.total_amt, s.payment_status, s.order_type
        FROM   sale s
               LEFT JOIN customer c ON s.cust_id = c.cust_id
        WHERE  s.branch_id = %s
        ORDER BY s.sale_date DESC
        LIMIT 10
    """, (branch_id,))

    low_stock = query("""
        SELECT p.product_name, bi.quantity, bi.reorder_level, bi.shelf_location
        FROM   branch_inventory bi
               JOIN product p USING (product_id)
        WHERE  bi.branch_id = %s AND bi.quantity <= bi.reorder_level
        ORDER BY bi.quantity ASC
    """, (branch_id,))

    branch_info = query(
        "SELECT branch_name FROM branch WHERE branch_id = %s",
        (branch_id,)
    )

    return templates.TemplateResponse(request, "employee_dashboard.html", {
        "branch_sales": branch_sales,
        "low_stock":    low_stock,
        "branch_name":  branch_info[0]["branch_name"] if branch_info else branch_id,
        "user_name":    session.get("user_name"),
        "position":     session.get("position"),
        "role":         "EMPLOYEE",
    })


@app.get("/admin/dashboard/employees", response_class=HTMLResponse)
def employees_page(request: Request, session=Depends(require_admin)):
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
               b.branch_name,
               d.dept_name
        FROM employee e
        LEFT JOIN branch b
            ON e.branch_id = b.branch_id
        LEFT JOIN department d
            ON e.dept_id = d.dept_id
        ORDER BY e.emp_name
    """)

    return templates.TemplateResponse(
        request,
        "admin/employees.html",
        {
            "employees": employees,
            "user_name": session.get("user_name"),
            "role": "ADMIN",
        }
    )

# ══════════════════════════════════════════════════════════════════════════════
#  CUSTOMER DASHBOARD  (protected — CUSTOMER only)
# ══════════════════════════════════════════════════════════════════════════════

@app.get("/customer/dashboard", response_class=HTMLResponse)
def customer_dashboard(request: Request, session=Depends(require_customer)):
    cust_id = session.get("user_id")

    my_orders = query("""
        SELECT s.sale_id,
               TO_CHAR(s.sale_date, 'DD Mon YYYY HH24:MI') AS sale_date,
               b.branch_name, s.total_amt,
               s.payment_status, s.order_type,
               oo.order_status, oo.delivery_address
        FROM   sale s
               JOIN branch b ON s.branch_id = b.branch_id
               LEFT JOIN online_order oo ON s.sale_id = oo.sale_id
        WHERE  s.cust_id = %s
        ORDER BY s.sale_date DESC
        LIMIT 10
    """, (cust_id,))

    cust_info = query(
        "SELECT cust_name, loyalty_points, membership_type FROM customer WHERE cust_id = %s",
        (cust_id,)
    )

    return templates.TemplateResponse(request, "customer_dashboard.html", {
        "my_orders":      my_orders,
        "user_name":      session.get("user_name"),
        "membership":     session.get("membership"),
        "loyalty_points": session.get("loyalty_points"),
        "role":           "CUSTOMER",
    })


# ══════════════════════════════════════════════════════════════════════════════
#  EXISTING ROUTES (unchanged — now also pass user context to templates)
# ══════════════════════════════════════════════════════════════════════════════
@app.get("/admin/dashboard/products", response_class=HTMLResponse)
def admin_products_page(request: Request, session=Depends(require_admin)):
    products = query("""
        SELECT p.product_id, p.product_name, p.brand,
               p.unit_price, p.unit, p.is_active,
               c.cat_name, s.supplier_name
        FROM   product p
               LEFT JOIN category c  USING (cat_id)
               LEFT JOIN supplier s  USING (supplier_id)
        ORDER BY p.product_name
    """)
    return templates.TemplateResponse(request, "admin/products.html", {
        "products":  products,
        "user_name": session.get("user_name"),
        "role":      session.get("role"),
    })


@app.get("/products", response_class=HTMLResponse)
def products_page(request: Request, session=Depends(require_login)):
    products = query("""
        SELECT p.product_id, p.product_name, p.brand,
               p.unit_price, p.unit, p.is_active,
               c.cat_name, s.supplier_name
        FROM   product p
               LEFT JOIN category c  USING (cat_id)
               LEFT JOIN supplier s  USING (supplier_id)
        ORDER BY p.product_name
    """)
    return templates.TemplateResponse(request, "products.html", {
        "products":  products,
        "user_name": session.get("user_name"),
        "role":      session.get("role"),
    })


@app.get("/sales", response_class=HTMLResponse)
def sales_page(request: Request, session=Depends(require_login)):
    # Employees see only their branch; admins see all
    if session.get("role") == "EMPLOYEE":
        where = f"WHERE s.branch_id = '{session.get('branch_id')}'"
    else:
        where = ""

    sales = query(f"""
        SELECT s.sale_id,
               TO_CHAR(s.sale_date, 'DD Mon YYYY HH24:MI') AS sale_date,
               b.branch_name,
               COALESCE(c.cust_name, 'Walk-in') AS customer,
               e.emp_name,
               s.subtotal, s.discount_amt, s.total_amt,
               s.payment_status, s.order_type
        FROM   sale s
               JOIN branch   b ON s.branch_id = b.branch_id
               LEFT JOIN customer c ON s.cust_id = c.cust_id
               JOIN employee e  ON s.emp_id    = e.emp_id
        {where}
        ORDER BY s.sale_date DESC
    """)
    return templates.TemplateResponse(request, "sales.html", {
        "sales":     sales,
        "user_name": session.get("user_name"),
        "role":      session.get("role"),
    })


@app.get("/admin/dashboard/customers", response_class=HTMLResponse)
def customers_page(request: Request, session=Depends(require_admin)):
    customers = query("""
        SELECT cust_id, cust_name, email, phone,
               gender, membership_type, loyalty_points,
               TO_CHAR(join_date, 'DD Mon YYYY') AS join_date
        FROM   customer
        ORDER BY cust_name
    """)
    return templates.TemplateResponse(request, "admin/customers.html", {
        "customers": customers,
        "user_name": session.get("user_name"),
        "role":      "ADMIN",
    })


@app.get("/admin/dashboard/branches", response_class=HTMLResponse)
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
    return templates.TemplateResponse(request, "admin/branches.html", {
        "branches":  branches,
        "user_name": session.get("user_name"),
        "role":      session.get("role"),
    })


@app.get("/inventory", response_class=HTMLResponse)
def inventory_page(request: Request, session=Depends(require_employee)):
    if session.get("role") == "EMPLOYEE":
        where = f"AND bi.branch_id = '{session.get('branch_id')}'"
    else:
        where = ""

    inventory = query(f"""
        SELECT bi.inv_id, b.branch_name, p.product_name,
               bi.quantity, bi.reorder_level, bi.shelf_location,
               TO_CHAR(bi.last_restocked, 'DD Mon YYYY') AS last_restocked,
               CASE WHEN bi.quantity <= bi.reorder_level
                    THEN 'LOW' ELSE 'OK' END AS stock_status
        FROM   branch_inventory bi
               JOIN branch  b USING (branch_id)
               JOIN product p USING (product_id)
        WHERE  1=1 {where}
        ORDER BY stock_status DESC, b.branch_name
    """)
    return templates.TemplateResponse(request, "inventory.html", {
        "inventory": inventory,
        "user_name": session.get("user_name"),
        "role":      session.get("role"),
    })

@app.get("/admin/dashboard/inventory", response_class=HTMLResponse)
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

    return templates.TemplateResponse(
        request,
        "admin/inventory.html",
        {
            "inventory": inventory,
            "user_name": session.get("user_name"),
            "role": "ADMIN",
        }
    )

@app.get("/discounts", response_class=HTMLResponse)
def discounts_page(request: Request, session=Depends(require_admin)):

    discounts = query("""
        SELECT
            d.discount_id,
            d.discount_name,
            d.discount_type,
            d.discount_value,

            p.product_name,
            c.cat_name,

            TO_CHAR(d.start_date,'DD Mon YYYY') AS start_date,
            TO_CHAR(d.end_date,'DD Mon YYYY')   AS end_date,

            CASE
                WHEN CURRENT_DATE BETWEEN d.start_date
                                     AND d.end_date
                    THEN 'ACTIVE'

                WHEN CURRENT_DATE < d.start_date
                    THEN 'UPCOMING'

                ELSE 'EXPIRED'
            END AS status

        FROM discount d

        LEFT JOIN product p
            ON d.product_id = p.product_id

        LEFT JOIN category c
            ON d.cat_id = c.cat_id

        ORDER BY d.start_date DESC
    """)

    return templates.TemplateResponse(
        request,
        "admin/discounts.html",
        {
            "discounts": discounts,
            "user_name": session.get("user_name"),
            "role": "ADMIN",
        }
    )

@app.get("/admin/dashboard/sales", response_class=HTMLResponse)
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

    return templates.TemplateResponse(
        request,
        "admin/sales.html",
        {
            "sales": sales,
            "role": "ADMIN",
            "user_name": session.get("user_name"),
        }
    )

@app.get("/admin/dashboard/profile", response_class=HTMLResponse)
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

    return templates.TemplateResponse(
        request,
        "admin/profile.html",
        {
            "admin": admin[0],
            "user_name": session.get("user_name"),
            "role": "ADMIN"
        }
    )

@app.post("/admin/dashboard/profile/update")
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

@app.post("/admin/dashboard/profile/password")
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

@app.get("/admin/dashboard/branches/manage")
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
    return templates.TemplateResponse(
        request,
        "admin/manage_branches.html",
        {
            "branches": branches,
            "unassigned_managers": unassigned_managers,  
            "cities": cities,
            "departments": departments,
            "user_name": session.get("user_name"),
            "role": "ADMIN",
        }
    )

@app.get("/admin/dashboard/suppliers")
def suppliers_page(
    request: Request,
    session=Depends(require_admin)
):

    suppliers = query("""
        SELECT *
        FROM supplier
        ORDER BY supplier_name
    """)

    return templates.TemplateResponse(
        request,
        "admin/suppliers.html",
        {
            "request": request,
            "suppliers": suppliers,
            "role": "ADMIN",
            "user_name": session.get("user_name"),
        },
        
    )