import os
from fastapi import FastAPI, Request, Form, HTTPException, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from auth import _hash, _verify
from branch_routes import branch_router
from database import query, execute
from customer import customer_router
from admin import admin_router
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
app.include_router(customer_router)
app.include_router(admin_router)


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