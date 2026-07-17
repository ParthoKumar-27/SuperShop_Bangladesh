"""Public storefront routes + discount helpers.

This module imports the app and templates objects from app_setup.py
and decorates them with the storefront endpoints (/, /search) plus
the discount-annotation helpers they call. Imported for side-effects
from main.py so the routes register on startup.
"""
import urllib.parse
import time

from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app_setup import app, templates
from database import query
from supabase_client import BUCKET, SUPABASE_URL

_CACHE = {}
_CACHE_TTL = 300 # 5 minutes

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


# ══════════════════════════════════════════════════════════════════════════════
#  ACTIVE HOT DEALS — products with a currently valid discount row
# ══════════════════════════════════════════════════════════════════════════════
def _fetch_hot_deals(limit: int = 20):
    """Return up to limit products that have an active discount row.

    Active = CURRENT_DATE between start_date and end_date. Handles both
    PERCENT and FLAT discounts and resolves category-wide discounts too.
    """
    now = time.time()
    cache_key = f"hot_deals_{limit}"
    if cache_key in _CACHE and now - _CACHE[cache_key]["ts"] < _CACHE_TTL:
        return _CACHE[cache_key]["data"]

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
    
    _CACHE[cache_key] = {"data": rows, "ts": now}
    return rows


# Per-product discount rows used by the storefront products grid. We LEFT JOIN
# discounts onto product rows, taking the best (largest absolute saving) row
# per product so a product covered by both a category-wide AND a product-level
# discount shows the better one. Each row gains:
#   sale_price    : float  (None if no active discount)
#   disc_label    : str    ("-15%" or "-৳30") for ribbons/badges
#   disc_type     : str    ('PERCENT' or 'FLAT' or None)
#   disc_value    : float  (raw discount number)
def _annotate_products_with_branch_availability(products, branch_id):
    """Annotate each product with whether it is in the selected branch and how
    many units are currently stocked there. Mutates in place; products with no
    matching `branch_inventory` row get quantity 0 and ``available_in_branch=False``.

    If no branch is selected yet (``branch_id`` is falsy) every product is left
    untouched and tagged ``available_in_branch=True`` — we don't want to bar
    the user from browsing before they've picked a branch; the cart-icon
    flow's existing branch-gate handles the "select first" UX.
    """
    if not products or not branch_id:
        for p in products:
            p["stock_at_branch"] = 0 if branch_id else None
            p["available_in_branch"] = not branch_id  # no branch → don't warn
        return products

    ids = [p["product_id"] for p in products]
    rows = query(
        """
        SELECT  bi.product_id,
                bi.quantity
        FROM    branch_inventory bi
        WHERE   bi.branch_id = %s
          AND   bi.product_id = ANY(%s)
        """,
        (branch_id, ids),
    ) or []
    on_hand = {r["product_id"]: int(r.get("quantity") or 0) for r in rows}
    for p in products:
        qty = on_hand.get(p["product_id"], 0)
        p["stock_at_branch"] = qty
        p["available_in_branch"] = qty > 0
    return products


def _annotate_products_with_discounts(products):
    """Mutate products in place — attach sale_price + disc_label where active."""
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
                CASE
                    WHEN d.discount_type = 'PERCENT' THEN
                         (p.unit_price * d.discount_value / 100.0)
                    ELSE LEAST(p.unit_price, d.discount_value)
                END AS saving
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


# ── Role → home redirect target (consumed by both / and the 403 handler) ──────
ROLE_HOME = {
    "ADMIN":    "/admin/dashboard",
    "EMPLOYEE": "/employee/branch/dashboard",
    "CUSTOMER": "/customer/dashboard",
}

def _get_categories():
    now = time.time()
    if "categories" in _CACHE and now - _CACHE["categories"]["ts"] < _CACHE_TTL:
        return _CACHE["categories"]["data"]
    
    categories = query("""
        SELECT cat_id, cat_name, parent_cat_id
        FROM   category
        ORDER  BY parent_cat_id NULLS FIRST, cat_name
    """)
    _CACHE["categories"] = {"data": categories, "ts": now}
    return categories

def _get_branches():
    now = time.time()
    if "branches" in _CACHE and now - _CACHE["branches"]["ts"] < _CACHE_TTL:
        return _CACHE["branches"]["data"]
    
    _branches_rows = query(
        "SELECT branch_id, branch_name FROM branch "
        "WHERE is_active = 'Y' ORDER BY branch_name"
    )
    data = list(_branches_rows or [])
    _CACHE["branches"] = {"data": data, "ts": now}
    return data

def _get_home_products():
    now = time.time()
    if "home_products" in _CACHE and now - _CACHE["home_products"]["ts"] < _CACHE_TTL:
        return _CACHE["home_products"]["data"]

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
    for _p in products:
        _p["image_url"] = _normalize_image_url(_p.get("image_url"))
    _annotate_products_with_discounts(products)
    # Branch availability is per-request — tag here with no branch so callers
    # override via `_annotate_products_with_branch_availability(products, bid)`.

    _CACHE["home_products"] = {"data": products, "ts": now}
    return products




# ══════════════════════════════════════════════════════════════════════════════
#  ROOT — public storefront (no login required).
#
#  Logged-in admin or employee who types "/" should *stay on the page they
#  were viewing*. We return an invisible 200 page that immediately runs
#  history.back() so the browser snaps back to the previous page, leaving
#  the URL bar pointing at their dashboard. Anonymous users and customers
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
    categories = _get_categories()

    # Branches shown in the "pick a branch" popup the first time a customer
    # adds anything to the cart from the storefront.
    _branches_list = _get_branches()
    _cart = request.session.get("cart", {}) if hasattr(request, "session") else {}

    # The cart is the single source of truth for the locked branch — each
    # entry stores the branch the item came from.  Derive selected_branch_id
    # from the cart first so a returning customer with items already in the
    # cart is NEVER prompted to re-pick a branch from the storefront.  Only
    # fall back to the session key (and then to nothing) when the cart is
    # empty or its entries don't carry a branch_id.
    def _cart_branch_id(cart):
        if not cart:
            return None
        for entry in cart.values():
            if isinstance(entry, dict) and entry.get("branch_id"):
                return entry["branch_id"]
        return None

    _cart_branch = _cart_branch_id(_cart)
    _session_branch_id = (
        request.session.get("selected_branch") if hasattr(request, "session") else None
    )
    _selected_branch_id = _cart_branch or _session_branch_id
    _selected_branch = (
        next((b for b in _branches_list if b["branch_id"] == _selected_branch_id), None)
        if _selected_branch_id
        else None
    )

    # All active products — visible to everyone
    products = _get_home_products()
    # Tag each product with whether it's in stock at the customer's selected
    # branch.  The card uses this to show a "Not available in this branch"
    # badge and to block the inline add-to-cart when the SKU is missing.
    _annotate_products_with_branch_availability(products, _selected_branch_id)

    # Same tagging for the hot-deals carousel so its inline cart icons respect
    # the selected branch too.
    hot_deals = _fetch_hot_deals(limit=20)
    _annotate_products_with_branch_availability(hot_deals, _selected_branch_id)

    # Cart count (from session) — shown as a badge on the topbar cart icon.
    # Cart entries may be the legacy shape {pid: qty} or the new shape
    # {pid: {"qty": n, "branch_id": bid}} — count qty in either case.
    # (`_cart` was already loaded above for branch-id derivation.)
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
#  PUBLIC SEARCH — same look as storefront, filtered by ?q= (no login needed)
# ══════════════════════════════════════════════════════════════════════════════
@app.get("/search", response_class=HTMLResponse)
def public_search(request: Request, q: str = ""):
    q = (q or "").strip()

    categories = _get_categories()

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

    # Branch availability tagging for the search results page as well, so a
    # customer who searched for an item at a branch that doesn't carry it
    # gets the same "Not available in this branch" badge.
    _branches_list = _get_branches()
    _cart = request.session.get("cart", {}) if hasattr(request, "session") else {}

    # Cart wins as the source of truth for the locked branch — same rule
    # used in customer.py /shop.  Without this, a returning customer whose
    # session["selected_branch"] was cleared but who still has items in the
    # cart would be incorrectly prompted to pick a branch here.
    def _cart_branch_id(cart):
        if not cart:
            return None
        for entry in cart.values():
            if isinstance(entry, dict) and entry.get("branch_id"):
                return entry["branch_id"]
        return None

    _selected_branch_id = (
        _cart_branch_id(_cart)
        or (request.session.get("selected_branch") if hasattr(request, "session") else None)
    )
    _selected_branch = (
        next((b for b in _branches_list if b["branch_id"] == _selected_branch_id), None)
        if _selected_branch_id
        else None
    )
    _annotate_products_with_branch_availability(products, _selected_branch_id)
    hot_deals = _fetch_hot_deals(limit=20)
    _annotate_products_with_branch_availability(hot_deals, _selected_branch_id)

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
            "hot_deals":  hot_deals,
            "logged_in":  bool(request.session.get("role")),
            "role":       request.session.get("role"),
            "search_query": q,
            "cart_count": cart_count,
            "branches":   _branches_list,
            "selected_branch": _selected_branch,
        }
    )