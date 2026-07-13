from fastapi import APIRouter, Request, Form, Depends, Query
from fastapi.responses import RedirectResponse, HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.templating import Jinja2Templates
from urllib.parse import quote

from httpcore import request
from database import query, execute
from auth import require_customer
from fastapi import FastAPI, Request, Form, HTTPException, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from datetime import date

customer_router = APIRouter(prefix="/customer", tags=["Customer"])
templates = Jinja2Templates(directory="templates")
from supabase_client import BUCKET as _BUCKET, SUPABASE_URL as _SUPABASE_URL

def _normalize_image_url(raw):
    """Build a public Supabase URL from either a full URL or a bare storage key."""
    if not raw:
        return None
    raw = str(raw).strip()
    if not raw:
        return None
    if raw.startswith(("http://", "https://", "//")):
        return raw
    key = raw.lstrip("/")
    if key.startswith(f"{_BUCKET}/"):
        key = key[len(_BUCKET) + 1:]
    return f"{_SUPABASE_URL.rstrip('/')}/storage/v1/object/public/{_BUCKET}/{key}"
# ══════════════════════════════════════════════════════════════════════════════
#  CUSTOMER DASHBOARD  (protected — CUSTOMER only)
# ══════════════════════════════════════════════════════════════════════════════
# ══════════════════════════════════════════════════════════════════════════════
#  CUSTOMER SHOP, CART & CHECKOUT
# ══════════════════════════════════════════════════════════════════════════════
# ══════════════════════════════════════════════════════════════════════════════
#  ROOT — redirect based on role
# ══════════════════════════════════════════════════════════════════════════════
def _next_id(prefix: str, table: str, column: str, total_len: int = 8) -> str:
    """Generate the next sequential ID like 'S-000001' for a VARCHAR(total_len) PK
    that follows the pattern '<prefix><zero-padded number>'."""
    width = total_len - len(prefix)
    rows = query(f"""
        SELECT COALESCE(MAX(CAST(SUBSTRING({column} FROM {len(prefix)+1}) AS INTEGER)), 0) + 1 AS next_num
        FROM {table}
        WHERE {column} ~ %s
    """, (f"^{prefix}[0-9]+$",))
    next_num = rows[0]["next_num"]
    return f"{prefix}{str(next_num).zfill(width)}"


# ══════════════════════════════════════════════════════════════════════════════
#  UTILITY FUNCTIONS
# ══════════════════════════════════════════════════════════════════════════════
def _next_id(prefix: str, table: str, column: str, total_len: int = 8) -> str:
    """Generate the next sequential ID like 'S-000001' for a VARCHAR(total_len) PK
    that follows the pattern '<prefix><zero-padded number>'."""
    width = total_len - len(prefix)
    rows = query(f"""
        SELECT COALESCE(MAX(CAST(SUBSTRING({column} FROM {len(prefix)+1}) AS INTEGER)), 0) + 1 AS next_num
        FROM {table}
        WHERE {column} ~ %s
    """, (f"^{prefix}[0-9]+$",))
    next_num = rows[0]["next_num"]
    return f"{prefix}{str(next_num).zfill(width)}"

def _get_active_discounts():
    rows = query("""
        SELECT discount_id, discount_name, discount_type, discount_value,
               product_id, cat_id
        FROM discount
        WHERE start_date <= CURRENT_DATE
          AND end_date >= CURRENT_DATE
    """)
    by_product = {}
    by_cat = {}
    for r in rows:
        if r["product_id"]:
            by_product[r["product_id"]] = r
        if r["cat_id"]:
            by_cat[r["cat_id"]] = r
    return by_product, by_cat

def _apply_discount(unit_price, product_id, cat_id, by_product, by_cat):
    disc = by_product.get(product_id) or by_cat.get(cat_id)
    if not disc:
        return float(unit_price), None
    price = float(unit_price)
    if disc["discount_type"] == "PERCENT":
        saved = price * float(disc["discount_value"]) / 100
        label = f"{disc['discount_value']}% off"
    else:
        saved = float(disc["discount_value"])
        label = f"৳{disc['discount_value']} off"
    return round(max(price - saved, 0), 2), label


def _refresh_customer_session(request: Request, session) -> None:
    """Re-read the live loyalty_points and membership_type from the DB and
    mirror them into the session so the persistent sidebar in
    customer/base.html always renders the *current* values instead of the
    stale ones captured at login time."""
    cust_id = session.get("user_id")
    if not cust_id:
        return
    rows = query(
        "SELECT membership_type, loyalty_points FROM customer WHERE cust_id = %s",
        (cust_id,),
    )
    if not rows:
        return
    request.session["membership"]     = rows[0].get("membership_type") or "REGULAR"
    request.session["loyalty_points"] = int(rows[0].get("loyalty_points") or 0)


def _customer_context(request: Request, session) -> dict:
    """Standard context keys every customer template needs so the sidebar
    (rendered from customer/base.html) keeps a single source of truth for
    name / membership / loyalty points."""
    _refresh_customer_session(request, session)
    return {
        "role":           "CUSTOMER",
        "user_name":      session.get("user_name"),
        "membership":     session.get("membership"),
        "loyalty_points": session.get("loyalty_points"),
    }

# ══════════════════════════════════════════════════════════════════════════════
#  CUSTOMER SHOP, CART & CHECKOUT
# ══════════════════════════════════════════════════════════════════════════════
@customer_router.post("/checkout")
def place_order(
    request: Request,
    branch_id: str = Form(default=None),
    payment_method: str = Form(...),
    expected_delivery: str = Form(...),  # Captured from user form
    delivery_address: str = Form(...),   # Captured from user form
    session=Depends(require_customer)
):
    cart = request.session.get("cart", {})
    if not cart:
        return RedirectResponse("/customer/shop", status_code=302)

    cust_id = session.get("user_id")

    if not branch_id:
        branch_id = request.session.get("selected_branch")
        
    if not branch_id:
        raise HTTPException(status_code=400, detail="No branch selected for checkout")

    by_product, by_cat = _get_active_discounts()

    products = query("""
        SELECT product_id, unit_price, cat_id
        FROM product
        WHERE product_id = ANY(%s) AND is_active = 'Y'
    """, (list(cart.keys()),))

    items = []
    subtotal = 0.0
    discount_amt = 0.0
    for p in products:
        pid = p["product_id"]
        qty = cart.get(pid, 0)
        if not qty:
            continue
        
        disc_price, _ = _apply_discount(p["unit_price"], pid, p["cat_id"], by_product, by_cat)
        original_line = float(p["unit_price"]) * qty
        disc_line = disc_price * qty
        
        subtotal += original_line
        discount_amt += original_line - disc_line
        items.append((pid, qty, disc_price, disc_line))

    if not items:
        return RedirectResponse("/customer/shop", status_code=302)

    # 4% tax on the product total (discount applied first), delivery fee excluded
    tax_amt = round((subtotal - discount_amt) * 0.04, 2)
    total_amt = round(subtotal - discount_amt + tax_amt, 2)
    payment_status = "PENDING" if payment_method == "CASH" else "PAID"

    emp_row = query("""
        SELECT emp_id FROM employee
        WHERE branch_id = %s AND is_active = 'Y'
        ORDER BY emp_id LIMIT 1
    """, (branch_id,))
    if not emp_row:
        emp_row = query("SELECT emp_id FROM employee WHERE is_active = 'Y' ORDER BY emp_id LIMIT 1")
    if not emp_row:
        raise HTTPException(status_code=500, detail="No employee available to process this order")
    emp_id = emp_row[0]["emp_id"]

    sale_id = _next_id("S-", "sale", "sale_id", 8)
    order_id = _next_id("O-", "online_order", "order_id", 8)

    execute("""
        INSERT INTO sale
            (sale_id, branch_id, cust_id, emp_id, order_type,
             subtotal, discount_amt, tax_amt, total_amt, payment_status)
        VALUES (%s, %s, %s, %s, 'ONLINE', %s, %s, %s, %s, %s)
    """, (sale_id, branch_id, cust_id, emp_id, subtotal, discount_amt, tax_amt, total_amt, payment_status))

    for pid, qty, unit_price, line_total in items:
        execute("""
            INSERT INTO sale_item (sale_id, product_id, quantity, unit_price, line_total)
            VALUES (%s, %s, %s, %s, %s)
        """, (sale_id, pid, qty, unit_price, line_total))

        # NEW — online orders never touched stock before
        execute("""
            UPDATE branch_inventory
            SET    quantity = quantity - %s
            WHERE  branch_id = %s AND product_id = %s
        """, (qty, branch_id, pid))

    # Saved with structural form values instead of placeholder text
    execute("""
        INSERT INTO online_order
            (order_id, cust_id, branch_id, sale_id, order_status, delivery_address, expected_delivery)
        VALUES (%s, %s, %s, %s, 'PLACED', %s, %s)
    """, (order_id, cust_id, branch_id, sale_id, delivery_address.strip(), expected_delivery.strip()))

    if payment_method != "CASH":
        payment_id = _next_id("PAY-", "payment", "payment_id", 8)
        execute("""
            INSERT INTO payment (payment_id, sale_id, amount, method, status)
            VALUES (%s, %s, %s, %s, 'SUCCESS')
        """, (payment_id, sale_id, total_amt, payment_method))

     # Points only once payment is actually confirmed PAID
        points_earned = int(total_amt // 10)
        if points_earned > 0:
            execute("""
                UPDATE customer SET loyalty_points = loyalty_points + %s
                WHERE cust_id = %s
            """, (points_earned, cust_id))
        # else: CASH (COD) — no payment row, no points yet. Both happen when
        

    # Award loyalty points: 1 point per 10 BDT spent
    # points_earned = int(total_amt // 10)
    # if points_earned > 0:
    #     execute("""
    #         UPDATE customer
    #         SET loyalty_points = COALESCE(loyalty_points, 0) + %s
    #         WHERE cust_id = %s
    #     """, (points_earned, cust_id))

    request.session["cart"] = {}
    _refresh_customer_session(request, session)

    return RedirectResponse("/customer/dashboard?msg=order_placed", status_code=302)


@customer_router.get("/invoice/{sale_id}", response_class=HTMLResponse)
def view_invoice(sale_id: str, request: Request, session=Depends(require_customer)):
    cust_id = session.get("user_id")

    sale_data = query("""
        SELECT s.sale_id, TO_CHAR(s.sale_date, 'DD Mon YYYY HH24:MI') AS sale_date,
               s.subtotal, s.discount_amt, s.tax_amt, s.total_amt, s.payment_status,
               b.branch_name, b.address AS branch_address, b.phone AS branch_phone
        FROM sale s
        JOIN branch b ON s.branch_id = b.branch_id
        LEFT JOIN online_order oo ON s.sale_id = oo.sale_id
        WHERE s.sale_id = %s AND s.cust_id = %s
    """, (sale_id, cust_id))

    if not sale_data:
        raise HTTPException(status_code=404, detail="Invoice record not found")

    invoice_items = query("""
        SELECT p.product_name, si.quantity, si.unit_price, si.line_total
        FROM sale_item si
        JOIN product p ON si.product_id = p.product_id
        WHERE si.sale_id = %s
    """, (sale_id,))

    return templates.TemplateResponse(
        request,
        "customer/invoice.html",
        {
            "sale": sale_data[0],
            "items": invoice_items,
            "user_name": session.get("user_name")
        }
    )


@customer_router.get("/invoice/{sale_id}/json")
def view_invoice_json(sale_id: str, session=Depends(require_customer)):
    cust_id = session.get("user_id")
    sale_data = query("""
        SELECT s.sale_id, TO_CHAR(s.sale_date, 'DD Mon YYYY HH24:MI') AS sale_date,
               s.subtotal, s.discount_amt, s.tax_amt, s.total_amt, s.payment_status,
               b.branch_name, b.address AS branch_address, b.phone AS branch_phone
        FROM sale s
        JOIN branch b ON s.branch_id = b.branch_id
        LEFT JOIN online_order oo ON s.sale_id = oo.sale_id
        WHERE s.sale_id = %s AND s.cust_id = %s
    """, (sale_id, cust_id))

    if not sale_data:
        raise HTTPException(status_code=404, detail="Invoice record not found")

    invoice_items = query("""
        SELECT p.product_name, si.quantity, si.unit_price, si.line_total
        FROM sale_item si
        JOIN product p ON si.product_id = p.product_id
        WHERE si.sale_id = %s
    """, (sale_id,))

    sale = sale_data[0]
    return JSONResponse({
        "sale_id": sale["sale_id"],
        "sale_date": sale["sale_date"],
        "branch_name": sale["branch_name"],
        "branch_address": sale["branch_address"],
        "branch_phone": sale["branch_phone"],
        "payment_status": sale["payment_status"],
        "subtotal": float(sale["subtotal"] or 0),
        "discount_amt": float(sale["discount_amt"] or 0),
        "tax_amt": float(sale["tax_amt"] or 0),
        "total_amt": float(sale["total_amt"] or 0),
        "items": [
            {
                "product_name": i["product_name"],
                "quantity": float(i["quantity"]),
                "unit_price": float(i["unit_price"]),
                "line_total": float(i["line_total"]),
            }
            for i in invoice_items
        ],
    })


@customer_router.post("/select-branch")
def select_branch(
    request: Request,
    branch_id: str = Form(...),
    session=Depends(require_customer)
):
    cart = request.session.get("cart", {})
    if cart:
        return RedirectResponse("/customer/shop?msg=branch_locked", status_code=302)

    request.session["selected_branch"] = branch_id
    return RedirectResponse("/customer/shop", status_code=302)


# @customer_router.get("/shop", response_class=HTMLResponse)
# def customer_shop(request: Request, session=Depends(require_customer)):
#     products = query("""
#         SELECT product_id, product_name, brand, unit_price, unit
#         FROM product
#         WHERE is_active = 'Y'
#         ORDER BY product_name
#     """)

#     return templates.TemplateResponse(request, "customer/shop.html", {
#         "products": products,
#         "role": "CUSTOMER",
#         "user_name": session.get("user_name"),
#     })

@customer_router.get("/shop", response_class=HTMLResponse)
def customer_shop(request: Request, session=Depends(require_customer)):
    branches = query("SELECT branch_id, branch_name FROM branch WHERE is_active = 'Y' ORDER BY branch_name")

    default_branch = next((b for b in branches if "dhanmondi" in b["branch_name"].lower()), branches[0] if branches else None)
    selected_branch_id = request.session.get("selected_branch")
    if not selected_branch_id and default_branch:
        selected_branch_id = default_branch["branch_id"]
        request.session["selected_branch"] = selected_branch_id
    selected_branch = next((b for b in branches if b["branch_id"] == selected_branch_id), None)

    # ── Categories (for the chip filter row) ────────────────────────────
    categories = query("""
        SELECT cat_id, cat_name, parent_cat_id
        FROM category
        ORDER BY parent_cat_id NULLS FIRST, cat_name
    """)

    # ── Category filter from ?cat= (accepts a parent or a leaf) ────────
    selected_cat = (request.query_params.get("cat") or "").strip()
    selected_cat_id = None
    selected_cat_name = None
    extra_cat_ids = []
    if selected_cat:
        # Resolve: could be a parent cat_id — include all descendants too.
        norm = selected_cat.upper().strip()
        match = next((c for c in categories if c["cat_id"].upper() == norm), None)
        if match:
            selected_cat_id = match["cat_id"]
            selected_cat_name = match["cat_name"]
            if match["parent_cat_id"] is None:
                # It's a parent — include all sub-categories
                extra_cat_ids = [c["cat_id"] for c in categories if c["parent_cat_id"] and c["parent_cat_id"].upper() == norm]

    raw_products = query("""
        SELECT p.product_id, p.product_name, p.brand, p.unit_price, p.unit, p.cat_id,
               p.image_url,
               bi.quantity,
               CASE WHEN bi.quantity <= bi.reorder_level THEN 'LOW' ELSE 'AVAILABLE' END AS stock_status
        FROM branch_inventory bi
        JOIN product p USING(product_id)
        WHERE bi.branch_id = %s AND p.is_active = 'Y' AND bi.quantity > 0
        ORDER BY p.product_name
    """, (selected_branch_id,))

    by_product, by_cat = _get_active_discounts()
    products = []
    for p in raw_products:
        if selected_cat_id is not None:
            in_filter = (p["cat_id"] and p["cat_id"].upper() == selected_cat_id.upper()) \
                        or (p["cat_id"] and p["cat_id"].upper() in {x.upper() for x in extra_cat_ids})
            if not in_filter:
                continue
        disc_price, disc_label = _apply_discount(p["unit_price"], p["product_id"], p["cat_id"], by_product, by_cat)
        p["image_url"] = _normalize_image_url(p.get("image_url"))
        products.append({**p, "disc_price": disc_price, "disc_label": disc_label})

    return templates.TemplateResponse(request, "customer/shop.html", {
        "products": products,
        "branches": branches,
        "selected_branch": selected_branch,
        "categories": categories,
        "selected_cat_id": selected_cat_id,
        "selected_cat_name": selected_cat_name,
        "cart_locked": len(request.session.get("cart", {})) > 0,
        **_customer_context(request, session),
    })


@customer_router.post("/cart/add")
async def add_to_cart(request: Request, session=Depends(require_customer)):
    """
    Add-to-cart endpoint.

    Accepts both regular form POSTs and AJAX (fetch) submissions:
      • Form POST  → 302 redirect to /customer/shop?msg=added  (existing behaviour)
      • Fetch POST → JSON { ok, cart_count, product_name, qty, cart_locked }
    AJAX responses let the shop page update without a full reload.
    """
    # ── Read body in a content-type-agnostic way ────────────────────────
    content_type = (request.headers.get("content-type") or "").lower()
    if "application/json" in content_type:
        try:
            payload = await request.json()
        except Exception:
            payload = {}
        product_id = (payload.get("product_id") or "").strip()
        try:
            quantity = int(payload.get("quantity") or 1)
        except (TypeError, ValueError):
            quantity = 1
    else:
        form = await request.form()
        product_id = (form.get("product_id") or "").strip()
        try:
            quantity = int(form.get("quantity") or 1)
        except (TypeError, ValueError):
            quantity = 1

    if not product_id:
        if "application/json" in content_type:
            return JSONResponse({"ok": False, "error": "Missing product_id"}, status_code=400)
        return RedirectResponse("/customer/shop?msg=invalid", status_code=302)

    quantity = max(1, quantity)

    # ── Update the session cart ──────────────────────────────────────────
    cart = request.session.get("cart", {})
    cart[product_id] = cart.get(product_id, 0) + quantity
    request.session["cart"] = cart

    cart_count = sum(cart.values())

    # ── Look up product name for the toast ───────────────────────────────
    row = query(
        "SELECT product_name FROM product WHERE product_id = %s",
        (product_id,),
    )
    product_name = row[0]["product_name"] if row else product_id

    # ── AJAX response ────────────────────────────────────────────────────
    if "application/json" in content_type:
        return JSONResponse({
            "ok": True,
            "product_id": product_id,
            "product_name": product_name,
            "qty": cart[product_id],
            "cart_count": cart_count,
        })

    # ── Classic form fallback ────────────────────────────────────────────
    return RedirectResponse("/customer/shop?msg=added", status_code=302)




@customer_router.get("/cart", response_class=HTMLResponse)
def view_cart(request: Request, session=Depends(require_customer)):
    cart = request.session.get("cart", {})
    items = []
    grand_total = 0.0
    total_savings = 0.0

    if cart:
        raw_products = query("""
            SELECT product_id, product_name, brand, unit_price, unit, cat_id
            FROM product
            WHERE product_id = ANY(%s)
        """, (list(cart.keys()),))

        by_product, by_cat = _get_active_discounts()

        for p in raw_products:
            qty = cart.get(p["product_id"], 0)
            disc_price, disc_label = _apply_discount(p["unit_price"], p["product_id"], p["cat_id"], by_product, by_cat)
            
            line_total = disc_price * qty
            original_line = float(p["unit_price"]) * qty
            
            total_savings += original_line - line_total
            grand_total += line_total
            
            items.append({
                **p, 
                "quantity": qty, 
                "line_total": line_total,
                "disc_price": disc_price, 
                "disc_label": disc_label,
                "original_price": float(p["unit_price"])
            })

    return templates.TemplateResponse(request, "customer/cart.html", {
        "items": items,
        "grand_total": grand_total,
        "total_savings": total_savings,
        **_customer_context(request, session),
    })



@customer_router.post("/cart/update")
def update_cart(
    request: Request,
    product_id: str = Form(...),
    quantity: int = Form(...),
    session=Depends(require_customer)
):
    cart = request.session.get("cart", {})

    if quantity <= 0:
        cart.pop(product_id, None)
    else:
        cart[product_id] = quantity

    request.session["cart"] = cart
    return RedirectResponse("/customer/cart", status_code=302)


@customer_router.post("/cart/remove")
def remove_from_cart(
    request: Request,
    product_id: str = Form(...),
    session=Depends(require_customer)
):
    cart = request.session.get("cart", {})
    cart.pop(product_id, None)
    request.session["cart"] = cart
    return RedirectResponse("/customer/cart", status_code=302)



@customer_router.get("/checkout", response_class=HTMLResponse)
def checkout_page(request: Request, session=Depends(require_customer)):
    cart = request.session.get("cart", {})
    if not cart:
        return RedirectResponse("/customer/shop", status_code=302)

    raw_products = query("""
        SELECT product_id, product_name, brand, unit_price, unit, cat_id
        FROM product WHERE product_id = ANY(%s)
    """, (list(cart.keys()),))

    by_product, by_cat = _get_active_discounts()
    items = []
    subtotal = 0.0
    total_savings = 0.0
    for p in raw_products:
        qty = cart.get(p["product_id"], 0)
        disc_price, disc_label = _apply_discount(p["unit_price"], p["product_id"], p["cat_id"], by_product, by_cat)
        line_total = disc_price * qty
        original_line = float(p["unit_price"]) * qty
        subtotal += line_total
        total_savings += original_line - line_total
        items.append({**p, "quantity": qty, "disc_price": disc_price,
                      "disc_label": disc_label, "line_total": line_total,
                      "original_price": float(p["unit_price"])})

    branches = query("SELECT branch_id, branch_name FROM branch WHERE is_active = 'Y' ORDER BY branch_name")
    selected_branch_id = request.session.get("selected_branch")
    selected_branch = next((b for b in branches if b["branch_id"] == selected_branch_id), None)

    tax_amt = round(subtotal * 0.04, 2)
    grand_total = round(subtotal + tax_amt, 2)

    return templates.TemplateResponse(request, "customer/checkout.html", {
        "items": items,
        "grand_total": grand_total,
        "product_total": subtotal,      # ← was missing
        "tax_amt": tax_amt,              # ← was missing
        "total_savings": total_savings,
        "branches": branches,
        "selected_branch_id": selected_branch_id,
        "selected_branch": selected_branch,
        "today": date.today().isoformat(),  # HTML5 min date controller
        **_customer_context(request, session),
    })




@customer_router.get("/inventory", response_class=HTMLResponse)
def customer_inventory(request: Request, branch_id: str = Query(default=None), session=Depends(require_customer)):
    branches = query("SELECT branch_id, branch_name FROM branch WHERE is_active = 'Y' ORDER BY branch_name")

    if branch_id:
        raw = query("""
            SELECT b.branch_name, p.product_id, p.product_name, p.unit_price, p.cat_id,
                   bi.quantity,
                   CASE WHEN bi.quantity <= bi.reorder_level THEN 'LOW' ELSE 'AVAILABLE' END AS stock_status
            FROM branch_inventory bi
            JOIN branch b USING(branch_id)
            JOIN product p USING(product_id)
            WHERE b.branch_id = %s
            ORDER BY p.product_name
        """, (branch_id,))
    else:
        raw = query("""
            SELECT b.branch_name, p.product_id, p.product_name, p.unit_price, p.cat_id,
                   bi.quantity,
                   CASE WHEN bi.quantity <= bi.reorder_level THEN 'LOW' ELSE 'AVAILABLE' END AS stock_status
            FROM branch_inventory bi
            JOIN branch b USING(branch_id)
            JOIN product p USING(product_id)
            ORDER BY b.branch_name, p.product_name
        """)

    by_product, by_cat = _get_active_discounts()
    inventory = []
    for item in raw:
        disc_price, disc_label = _apply_discount(item["unit_price"], item["product_id"], item["cat_id"], by_product, by_cat)
        inventory.append({**item, "disc_price": disc_price, "disc_label": disc_label})

    return templates.TemplateResponse(request, "customer/inventory.html", {
        "inventory": inventory,
        "branches": branches,
        "selected_branch": branch_id,
        "role": "CUSTOMER",
        "user_name": session.get("user_name"),
    })



@customer_router.get("/branches", response_class=HTMLResponse)
def customer_branches(
    request: Request,
    session=Depends(require_customer)
):

    branches = query("""
        SELECT
            b.branch_id,
            b.branch_name,
            c.city_name,
            b.address,
            b.phone,
            b.open_time,
            b.close_time,
            b.is_active
        FROM branch b
        JOIN city c
            ON b.city_id=c.city_id
        ORDER BY b.branch_name
    """)

    return templates.TemplateResponse(
        request,
        "customer/branches.html",
        {
            "branches": branches,
            **_customer_context(request, session),
        }
    )


# ══════════════════════════════════════════════════════════════════════════════
#  CUSTOMER PROFILE — view & update personal info
# ══════════════════════════════════════════════════════════════════════════════
@customer_router.get("/profile", response_class=HTMLResponse)
def customer_profile(request: Request, session=Depends(require_customer)):
    cust_id = session.get("user_id")

    rows = query("""
        SELECT cust_id, cust_name, email, phone, address, dob, gender,
               loyalty_points, membership_type, join_date
        FROM customer
        WHERE cust_id = %s
    """, (cust_id,))

    if not rows:
        return RedirectResponse("/auth/login", status_code=302)

    profile = rows[0]
    # dob is a date object in psycopg2 — convert to ISO so the <input type="date">
    # value attribute picks it up correctly.
    if profile.get("dob"):
        profile["dob"] = profile["dob"].isoformat()

    return templates.TemplateResponse(request, "customer/profile.html", {
        "profile":        profile,
        **_customer_context(request, session),
        "msg":            request.query_params.get("msg"),
    })


@customer_router.post("/profile")
def customer_profile_update(
    request: Request,
    cust_name: str = Form(...),
    phone:     str = Form(...),
    email:     str = Form(""),
    address:   str = Form(""),
    dob:       str = Form(""),
    gender:    str = Form(""),
    session=Depends(require_customer),
):
    cust_id = session.get("user_id")

    # Normalize / validate
    cust_name = cust_name.strip()
    phone     = phone.strip()
    email     = email.strip() or None
    address   = address.strip() or None
    dob       = dob.strip() or None
    gender    = gender.strip().upper() or None
    if gender and gender not in ("M", "F"):
        gender = None

    if not cust_name or not phone:
        return RedirectResponse(
            f"/customer/profile?error=Name+and+phone+are+required",
            status_code=302,
        )

    # Uniqueness check on email (DB has UNIQUE constraint) so we can return a
    # friendly message instead of a 500 from the INSERT/UPDATE raising.
    if email:
        clash = query(
            "SELECT cust_id FROM customer WHERE email = %s AND cust_id <> %s",
            (email, cust_id),
        )
        if clash:
            return RedirectResponse(
                "/customer/profile?error=This+email+is+already+used+by+another+account",
                status_code=302,
            )

    clash_phone = query(
        "SELECT cust_id FROM customer WHERE phone = %s AND cust_id <> %s",
        (phone, cust_id),
    )
    if clash_phone:
        return RedirectResponse(
            "/customer/profile?error=This+phone+number+is+already+used+by+another+account",
            status_code=302,
        )

    try:
        execute("""
            UPDATE customer
               SET cust_name = %s,
                   email     = %s,
                   phone     = %s,
                   address   = %s,
                   dob       = %s,
                   gender    = %s
             WHERE cust_id = %s
        """, (cust_name, email, phone, address, dob, gender, cust_id))
    except Exception as e:
        return RedirectResponse(
            f"/customer/profile?error=Could+not+update:+{quote(str(e))}",
            status_code=302,
        )

    # Keep session display name in sync
    request.session["user_name"] = cust_name
    return RedirectResponse("/customer/profile?msg=profile_updated", status_code=302)


@customer_router.post("/delete-account")
def delete_customer_account(
    request: Request,
    session=Depends(require_customer)
):
    cust_id = session.get("user_id")

    # Removes login access only — customer row, loyalty points and
    # purchase history are fully preserved.
    # Re-registering with the same phone will reconnect to all existing data
    # via the ghost-customer path in /auth/customer/register.
    execute("""
        DELETE FROM app_user
        WHERE ref_id = %s AND role = 'CUSTOMER'
    """, (cust_id,))

    request.session.clear()
    return RedirectResponse("/?msg=account_deleted", status_code=302)



@customer_router.get("/dashboard", response_class=HTMLResponse)
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

    # Attach the first 4 items per order so the dashboard can render product
    # chips inline (Amazon-style "Your Orders" rows). One round-trip per order
    # is acceptable since the LIMIT is small.
    for o in my_orders:
        o["items"] = query(
            """
            SELECT p.product_name, si.quantity, si.line_total
            FROM   sale_item si
            JOIN   product   p ON si.product_id = p.product_id
            WHERE  si.sale_id = %s
            ORDER  BY si.sale_id
            LIMIT  4
            """,
            (o["sale_id"],),
        )

    cust_info = query(
        "SELECT cust_name, loyalty_points, membership_type FROM customer WHERE cust_id = %s",
        (cust_id,)
    )

    return templates.TemplateResponse(request, "customer/dashboard.html", {
        "my_orders":      my_orders,
        **_customer_context(request, session),
    })

# ══════════════════════════════════════════════════════════════════════════════
#  CATEGORY PAGE — products filtered by category (and its subcategories)
# ══════════════════════════════════════════════════════════════════════════════
@customer_router.get("/category/{cat_id}", response_class=HTMLResponse)
def category_page(request: Request, cat_id: str):
    category = query("""
        SELECT cat_id, cat_name, parent_cat_id, description
        FROM category
        WHERE cat_id = %s
    """, (cat_id,))

    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    products = query("""
        SELECT p.product_id,
               p.product_name,
               p.brand,
               p.unit_price,
               p.unit
        FROM product p
        WHERE p.is_active = 'Y'
          AND (
                p.cat_id = %s
             OR p.cat_id IN (SELECT cat_id FROM category WHERE parent_cat_id = %s)
          )
        ORDER BY p.product_name
    """, (cat_id, cat_id))

    return templates.TemplateResponse(
        request,
        "category.html",
        {
            "products": products,
            "category": category[0],
            "logged_in": bool(request.session.get("role")),
            "role": request.session.get("role"),
        }
    )


@customer_router.post("/order/hide/{sale_id}")
def hide_order(sale_id: str, session=Depends(require_customer)):
    cust_id = session.get("user_id")
    
    execute("""
        UPDATE sale
        SET hidden_by_customer = 'Y'
        WHERE sale_id = %s AND cust_id = %s
    """, (sale_id, cust_id))
    
    return RedirectResponse("/customer/dashboard?msg=order_hidden", status_code=302)