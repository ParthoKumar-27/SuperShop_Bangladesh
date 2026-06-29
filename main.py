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
from auth import auth_router
from employee import employee_router


# ── App setup ──────────────────────────────────────────────────────────────────
app = FastAPI(
    title="SuperShop Bangladesh",
    description="Multi-branch retail management system",
    version="1.0.0"
)

# ── Session middleware ─────────────────────────────────────────────────────────
app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SECRET_KEY", "change-this-in-production-32chars"),
    max_age=3600 * 8,
    https_only=False,
)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# ── Routers ────────────────────────────────────────────────────────────────────
app.include_router(auth_router)
app.include_router(branch_router)
app.include_router(customer_router)
app.include_router(admin_router)
app.include_router(employee_router)


# ══════════════════════════════════════════════════════════════════════════════
#  ROOT — public storefront (no login required)
# ══════════════════════════════════════════════════════════════════════════════
@app.get("/", response_class=HTMLResponse)
def storefront(request: Request):
    # All categories ordered: top-level first, then sub-categories
    categories = query("""
        SELECT cat_id, cat_name, parent_cat_id
        FROM   category
        ORDER  BY parent_cat_id NULLS FIRST, cat_name
    """)

    # All active products — visible to everyone
    products = query("""
        SELECT p.product_id,
               p.product_name,
               p.brand,
               p.unit_price,
               p.unit,
               p.cat_id,
               c.cat_name AS category
        FROM   product   p
        LEFT   JOIN category c ON p.cat_id = c.cat_id
        WHERE  p.is_active = 'Y'
        ORDER  BY p.product_name
    """)

    return templates.TemplateResponse(
        request,
        "storefront.html",
        {
            "categories": categories,
            "products":   products,
            "logged_in":  bool(request.session.get("role")),
            "role":       request.session.get("role"),
        }
    )