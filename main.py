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


# ── No-cache middleware ────────────────────────────────────────────────────────
# Logout-then-back-button can otherwise restore authenticated pages from the
# browser's bfcache or disk cache. Tell the browser not to cache any HTML
# response; combined with the `pageshow` handler in the templates, this
# forces a hard reload any time the user navigates back to an auth'd page.
class NoCacheHTMLMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                ct = b""
                for k, v in headers:
                    if k == b"content-type":
                        ct = v.lower()
                        break
                # Apply no-cache only to HTML responses — leave JSON / images
                # / CSS / JS untouched so the rest of the site stays fast.
                if ct.startswith(b"text/html"):
                    headers += [
                        (b"cache-control", b"no-store, no-cache, must-revalidate, private"),
                        (b"pragma",        b"no-cache"),
                        (b"expires",       b"0"),
                    ]
                message["headers"] = headers
            await send(message)

        await self.app(scope, receive, send_wrapper)


app.add_middleware(NoCacheHTMLMiddleware)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")
templates.env.filters["sum_cart_qty"] = lambda c: (
    0 if not c else sum(
        (int(v.get("qty", 0)) if isinstance(v, dict) else int(v or 0))
        for v in c.values()
    )
)

# ── Routers ────────────────────────────────────────────────────────────────────
app.include_router(auth_router)
app.include_router(branch_router)
app.include_router(customer_router)
app.include_router(admin_router)
app.include_router(employee_router)


# ══════════════════════════════════════════════════════════════════════════════
#  ACTIVE HOT DEALS — products with a currently valid discount row
# ══════════════════════════════════════════════════════════════════════════════
def _fetch_hot_deals(limit: int = 20):
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


# Per-product discount rows used by the storefront products grid. We LEFT JOIN
# discounts onto product rows, taking the best (largest absolute saving) row
# per product so a product covered by both a category-wide AND a product-level
# discount shows the better one. Each row gains:
#   sale_price    : float  (None if no active discount)
#   disc_label    : str    ("-15%" or "-৳30") for ribbons/badges
#   disc_type     : str    ('PERCENT' or 'FLAT' or None)
#   disc_value    : float  (raw discount number)
def _annotate_products_with_discounts(products):
    """Mutate `products` in place — attach sale_price + disc_label where active."""
    if not products:
        return products
    ids = [p["product_id"] for p in products]
    rows = query(
        """
        SELECT  d.product_id  AS dp_id,
                d.cat_id     AS dc_id,
                d.discount_type,
                d.discount_value,
                p.product_id,
                p.unit_price,
                CASE
                    WHEN d.discount_type = 'PERCENT' THEN
                         GREATEST(0, p.unit_price - (p.unit_price * d.discount_value / 100.0))
                    ELSE
                         GREATEST(0, p.unit_price - d.discount_value)
                END AS sale_price,
                (p.unit_price - CASE
                    WHEN d.discount_type = 'PERCENT' THEN
                         (p.unit_price * d.discount_value / 100.0)
                    ELSE LEAST(p.unit_price, d.discount_value)
                END) AS saving
        FROM    discount d
        JOIN    product  p ON p.product_id = d.product_id
                           OR  p.cat_id    = d.cat_id
        WHERE   CURRENT_DATE BETWEEN d.start_date AND d.end_date
          AND   p.is_active  = 'Y'
          AND   p.product_id = ANY(%s)
        """,
        (ids,),
    ) or []

    best = {}
    for r in rows:
        pid = r["product_id"]
        cur = best.get(pid)
        if cur is None or (r.get("saving") or 0) > (cur.get("saving") or 0):
            best[pid] = r

    for p in products:
        b = best.get(p["product_id"])
        if not b:
            p["sale_price"] = None
            p["disc_label"] = None
            p["disc_type"]  = None
            p["disc_value"] = None
            continue
        p["sale_price"] = float(b["sale_price"])
        p["disc_type"]  = b["discount_type"]
        p["disc_value"] = float(b["discount_value"])
        if b["discount_type"] == "PERCENT":
            # Round to nearest int percent for a clean badge
            pct = int(round(float(b["discount_value"])))
            p["disc_label"] = f"-{pct}%"
        else:
            # FLAT
            p["disc_label"] = f"-৳{int(round(float(b['discount_value'])))}"
    return products


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
    # Attach per-product discount data so cards can show sale price + ribbon
    _annotate_products_with_discounts(products)

    hot_deals = _fetch_hot_deals(limit=20)

    # Cart count (from session) — shown as a badge on the topbar cart icon.
    # Cart entries may be the legacy shape {pid: qty} or the new shape
    # {pid: {"qty": n, "branch_id": bid}} — count qty in either case.
    _cart = request.session.get("cart", {}) if hasattr(request, "session") else {}
    if isinstance(_cart, dict):
        cart_count = 0
        for _entry in _cart.values():
            if isinstance(_entry, dict):
                cart_count += int(_entry.get("qty", 0) or 0)
            else:
                cart_count += int(_entry or 0)
    else:
        cart_count = 0

    # Branches shown in the "pick a branch" popup the first time a customer
    # adds anything to the cart from the storefront.
    _branches_rows = query(
        "SELECT branch_id, branch_name FROM branch "
        "WHERE is_active = 'Y' ORDER BY branch_name"
    )
    _branches_list = list(_branches_rows or [])
    _selected_branch_id = (
        request.session.get("selected_branch") if hasattr(request, "session") else None
    )
    _selected_branch = (
        next((b for b in _branches_list if b["branch_id"] == _selected_branch_id), None)
        if _selected_branch_id
        else None
    )

    return templates.TemplateResponse(
        request,
        "storefront.html",
        {
            "categories":        categories,
            "products":          products,
            "hot_deals":         hot_deals,
            "logged_in":         bool(role),
            "role":              role,
            "cart_count":        cart_count,
            "branches":          _branches_list,
            "selected_branch":   _selected_branch,
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
    _annotate_products_with_discounts(products)

    _cart = request.session.get("cart", {}) if hasattr(request, "session") else {}
    if isinstance(_cart, dict):
        cart_count = 0
        for _entry in _cart.values():
            if isinstance(_entry, dict):
                cart_count += int(_entry.get("qty", 0) or 0)
            else:
                cart_count += int(_entry or 0)
    else:
        cart_count = 0

    return templates.TemplateResponse(
        request,
        "storefront.html",
        {
            "categories": categories,
            "products":   products,
            "hot_deals":  _fetch_hot_deals(limit=20),
            "logged_in":  bool(request.session.get("role")),
            "role":       request.session.get("role"),
            "search_query": q,
            "cart_count": cart_count,
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