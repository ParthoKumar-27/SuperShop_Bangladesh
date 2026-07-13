import os
import urllib.parse
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import RedirectResponse
from branch_routes import branch_router
from database import query, execute
from customer import customer_router
from admin import admin_router
from auth import auth_router
from employee import employee_router
from database import close_pool
from supabase_client import BUCKET, SUPABASE_URL

# ── Image URL helper ──────────────────────────────────────────────────────────
# Stored values may be:
#   1. full public URL  (e.g. https://xyz.supabase.co/storage/v1/object/public/Images/abc.jpg)
#   2. bare storage key (e.g. products/P-0001.jpg) — from older seed data
#   3. NULL
# Always return something the browser can <img src="..."> against, or None.
def _normalize_image_url(raw: str | None) -> str | None:
    if not raw:
        return None
    raw = raw.strip()
    if not raw:
        return None
    if raw.startswith(("http://", "https://", "//")):
        return raw
    # bare key → build public URL from configured bucket
    key = raw.lstrip("/")
    if key.startswith(f"{BUCKET}/"):
        key = key[len(BUCKET) + 1:]
    return f"{SUPABASE_URL.rstrip('/')}/storage/v1/object/public/{BUCKET}/{key}"

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
    https_only=True,
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
#  ACTIVE HOT DEALS — products with a currently valid discount row
# ══════════════════════════════════════════════════════════════════════════════
def _fetch_hot_deals(limit: int = 6):
    """Return up to `limit` products that have an active discount row.

    Active = CURRENT_DATE between start_date and end_date. Handles both
    PERCENT and FLAT discounts and resolves category-wide discounts too.
    """
    rows = query(
        """
        SELECT  p.product_id,
                p.product_name,
                p.brand,
                p.unit_price,
                p.unit,
                p.image_url,
                d.discount_id,
                d.discount_name,
                d.discount_type,
                d.discount_value,
                d.end_date,
                CASE
                    WHEN d.discount_type = 'PERCENT' THEN
                         GREATEST(0, p.unit_price - (p.unit_price * d.discount_value / 100.0))
                    ELSE
                         GREATEST(0, p.unit_price - d.discount_value)
                END AS sale_price
        FROM    discount  d
        JOIN    product   p ON p.product_id = d.product_id
                            OR  p.cat_id    = d.cat_id
        WHERE   CURRENT_DATE BETWEEN d.start_date AND d.end_date
          AND   p.is_active  = 'Y'
        ORDER BY d.end_date ASC, p.product_name
        LIMIT  %s
        """,
        (limit,),
    ) or []
    for _r in rows:
        _r["image_url"] = _normalize_image_url(_r.get("image_url"))
    return rows


# ══════════════════════════════════════════════════════════════════════════════
#  ROOT — public storefront (no login required).
#
#  Logged-in admin or employee who types "/" should *stay on the page they
#  were viewing*. We return an invisible 200 page that immediately runs
#  `history.back()` so the browser snaps back to the previous page, leaving
#  the URL bar pointing at *their* dashboard. Anonymous users and customers
#  see the storefront as usual.
# ══════════════════════════════════════════════════════════════════════════════
@app.get("/", response_class=HTMLResponse)
def storefront(request: Request):
    role = (request.session.get("role") if hasattr(request, "session") else None)

    # ── Logged-in admin/employee: keep them on the page they came from ──────
    if role in ("ADMIN", "EMPLOYEE"):
        back_url = request.headers.get("referer") or ROLE_HOME.get(role, "/")
        safe = urllib.parse.quote(back_url, safe="/:?&=")
        body = (
            "<!doctype html><html><head><meta charset='utf-8'>"
            "<style>html,body{margin:0;background:#f8faf9}</style>"
            "<script>history.back();setTimeout(function(){location.replace("
            f"{repr(safe)}"
            ")},50);</script></head><body></body></html>"
        )
        return HTMLResponse(content=body, status_code=200)

    # ── Anonymous or customer: render the storefront ─────────────────────────
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
               p.image_url,
               c.cat_name AS category
        FROM   product   p
        LEFT   JOIN category c ON p.cat_id = c.cat_id
        WHERE  p.is_active = 'Y'
        ORDER  BY p.product_name
    """)
    # Normalize image_url so any legacy bare-key values still render in <img src>
    for _p in products:
        _p["image_url"] = _normalize_image_url(_p.get("image_url"))

    hot_deals = _fetch_hot_deals(limit=6)

    return templates.TemplateResponse(
        request,
        "storefront.html",
        {
            "categories": categories,
            "products":   products,
            "hot_deals":  hot_deals,
            "logged_in":  bool(role),
            "role":       role,
        }
    )


# ══════════════════════════════════════════════════════════════════════════════
#  PUBLIC SEARCH — same look as storefront, filtered by `?q=` (no login needed)
# ══════════════════════════════════════════════════════════════════════════════
@app.get("/search", response_class=HTMLResponse)
def public_search(request: Request, q: str = ""):
    q = (q or "").strip()

    categories = query("""
        SELECT cat_id, cat_name, parent_cat_id
        FROM   category
        ORDER  BY parent_cat_id NULLS FIRST, cat_name
    """)

    if q:
        like = f"%{q}%"
        products = query("""
            SELECT p.product_id,
                   p.product_name,
                   p.brand,
                   p.unit_price,
                   p.unit,
                   p.cat_id,
                   p.image_url,
                   c.cat_name AS category
            FROM   product   p
            LEFT   JOIN category c ON p.cat_id = c.cat_id
            WHERE  p.is_active = 'Y'
              AND  (p.product_name ILIKE %s OR p.brand ILIKE %s OR c.cat_name ILIKE %s)
            ORDER  BY p.product_name
        """, (like, like, like))
    else:
        products = []

    for _p in products:
        _p["image_url"] = _normalize_image_url(_p.get("image_url"))

    return templates.TemplateResponse(
        request,
        "storefront.html",
        {
            "categories": categories,
            "products":   products,
            "hot_deals":  _fetch_hot_deals(limit=6),
            "logged_in":  bool(request.session.get("role")),
            "role":       request.session.get("role"),
            "search_query": q,
        }
    )

# ── Error handlers ─────────────────────────────────────────────────────────────
ROLE_HOME = {
    "ADMIN":    "/admin/dashboard",
    "EMPLOYEE": "/employee/branch/dashboard",
    "CUSTOMER": "/customer/dashboard",
}


@app.exception_handler(403)
async def _forbidden_handler(request: Request, exc):
    """Auth failure handler.

    - Anonymous users  → redirect to login (with ?next=<original>).
    - Logged-in users who URL-edit into a page they're not allowed to
      access (admin → employee URL, employee → other employee/admin URL,
      etc.) → the user stays on the page they were already viewing.
      We return a tiny invisible HTML page that immediately runs
      `history.back()` so the browser snaps back to where they came from,
      leaving the URL bar pointing at *their* dashboard (not the forbidden
      URL they typed). No new page is rendered.
    """
    sess = getattr(request, "session", {}) or {}
    role = sess.get("role")

    # ── Anonymous: must log in first ────────────────────────────────────────
    if not role:
        path = request.url.path or "/"
        qs   = request.url.query or ""
        next_url = f"{path}?{qs}" if qs else path
        return RedirectResponse(
            url=f"/auth/login?next={urllib.parse.quote(next_url, safe='/')}",
            status_code=302,
        )

    # ── Already logged in: bounce silently back to the page they came from ──
    # Returning status 403 keeps it from being cached; the inline <script>
    # navigates back before the user sees anything.
    back_url = request.headers.get("referer") or ROLE_HOME.get(role, "/")
    safe = urllib.parse.quote(back_url, safe="/:?&=")
    body = (
        "<!doctype html><html><head><meta charset='utf-8'>"
        "<style>html,body{margin:0;background:#f8faf9}</style>"
        "<script>history.back();setTimeout(function(){location.replace("
        f"{repr(safe)}"
        ")},50);</script></head><body></body></html>"
    )
    return HTMLResponse(content=body, status_code=403)


@app.exception_handler(404)
async def _not_found_handler(request: Request, exc):
    """Render a friendly 404 page (we don't want the default Starlette plain text)."""
    role = request.session.get("role") if hasattr(request, "session") else None
    return templates.TemplateResponse(
        request,
        "errors/404.html",
        {
            "request_path":  request.url.path,
            "role":          role,
            "is_logged_in":  bool(role),
        },
        status_code=404,
    )


@app.on_event("shutdown")
def shutdown():
    close_pool()