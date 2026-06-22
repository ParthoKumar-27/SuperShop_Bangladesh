import os
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from branch_routes import branch_router
from database import query, execute
from customer import customer_router
from admin import admin_router
from auth import (
    auth_router
)
from employee import employee_router
    

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
app.include_router(employee_router)

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