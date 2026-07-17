from fastapi import APIRouter, Request, Form, Depends, Query
from fastapi.responses import RedirectResponse, HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.templating import Jinja2Templates
from urllib.parse import quote

from httpcore import request
from database import query, execute
from auth import require_customer, _hash, _verify
from notifications import notify_branch_manager
from fastapi import FastAPI, Request, Form, HTTPException, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from datetime import date

customer_router = APIRouter(prefix="/customer", tags=["Customer"])
templates = Jinja2Templates(directory="templates")
templates.env.filters["sum_cart_qty"] = lambda c: _cart_qty_sum(c or {})
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
def _cancel_and_refund_customer(order_id: str):
    """Same logic as employee._cancel_and_refund, but lives in this module
    so customer.py has no cross-router import on employee.py.

    In one transaction:
      • online_order.order_status → 'CANCELLED'
      • sale.payment_status       → 'CANCELLED'
      • branch_inventory          ← restocked per item
      • payment.status            ← 'REFUNDED' (only if money was taken)
      • customer.loyalty_points   ← decremented (only if refunded)

    Idempotent: if the sale is already CANCELLED we no-op, but we still
    ensure the online_order flag is CANCELLED so the dashboard's Cancel
    button disappears reliably even if a prior partial run left it
    stranded in PLACED."""
    row = query("""
        SELECT s.sale_id, s.cust_id, s.total_amt, s.payment_status,
               oo.order_status
        FROM   online_order oo JOIN sale s ON oo.sale_id = s.sale_id
        WHERE  oo.order_id = %s
    """, (order_id,))
    if not row:
        return None
    row = row[0]
    sale_id, cust_id = row["sale_id"], row["cust_id"]

    if row["payment_status"] == "CANCELLED":
        # Sale already cancelled — make sure the online_order flag is
        # also CANCELLED so the row no longer advertises Cancel button.
        if (row["order_status"] or "").upper() != "CANCELLED":
            execute(
                "UPDATE online_order SET order_status = 'CANCELLED' "
                "WHERE order_id = %s",
                (order_id,),
            )
        return sale_id  # already handled

    items = query("SELECT product_id, quantity FROM sale_item WHERE sale_id = %s", (sale_id,))
    for it in items:
        execute("""
            UPDATE branch_inventory bi
            SET    quantity = quantity + %s
            FROM   online_order oo
            WHERE  bi.product_id = %s AND bi.branch_id = oo.branch_id
              AND  oo.order_id = %s
        """, (it["quantity"], it["product_id"], order_id))

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

    execute("UPDATE sale SET payment_status = 'CANCELLED' WHERE sale_id = %s", (sale_id,))
    execute(
        "UPDATE online_order SET order_status = 'CANCELLED' WHERE order_id = %s",
        (order_id,),
    )
    return sale_id
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


def _cart_total(cart: dict) -> float:
    """Sum of (qty × discounted unit_price) across all items in the cart.
    Uses the same discount table as the cart/checkout pages so the locked
    banner on /shop shows a number that matches what checkout would charge.

    Handles BOTH the legacy flat shape {pid: qty} and the new shape
    {pid: {"qty": n, "branch_id": bid}}, so older sessions survive."""
    if not cart:
        return 0.0
    rows = query(
        "SELECT product_id, unit_price, cat_id FROM product "
        "WHERE product_id = ANY(%s)",
        (list(cart.keys()),),
    )
    by_product, by_cat = _get_active_discounts()
    total = 0.0
    for r in rows:
        pid = r["product_id"]
        entry = cart.get(pid)
        if entry is None:
            continue
        qty = entry["qty"] if isinstance(entry, dict) else entry
        if not qty:
            continue
        disc_price, _ = _apply_discount(
            r["unit_price"], pid, r["cat_id"], by_product, by_cat,
        )
        total += disc_price * qty
    return round(total, 2)


def _cart_locked_branch(cart: dict) -> str | None:
    """Return the branch_id the cart is locked to, or None when empty.

    The cart is the single source of truth for the locked branch — each
    cart entry stores the branch the item came from.  This makes it
    impossible for the page to display one branch while rendering
    products from another, because the cart always wins.

    Handles BOTH the legacy flat shape {pid: qty} and the new shape
    {pid: {"qty": n, "branch_id": bid}}."""
    if not cart:
        return None
    for entry in cart.values():
        if isinstance(entry, dict) and entry.get("branch_id"):
            return entry["branch_id"]
    # Legacy shape — no branch_id on entries.
    return None


def _cart_iter(cart: dict):
    """Iterate over a cart yielding (product_id, qty, branch_id) tuples.
    Works for both the legacy {pid: qty} and the new {pid: {qty, branch_id}}
    shapes, so the rest of the codebase keeps reading naturally."""
    for pid, entry in cart.items():
        if isinstance(entry, dict):
            yield pid, int(entry.get("qty", 0)), entry.get("branch_id")
        else:
            yield pid, int(entry or 0), None


def _cart_qty(cart: dict, pid: str) -> int:
    entry = cart.get(pid)
    if entry is None:
        return 0
    if isinstance(entry, dict):
        return int(entry.get("qty", 0))
    return int(entry or 0)


def _cart_qty_sum(cart: dict) -> int:
    """Shape-aware cart-count used by the topbar badge.

    Sums quantities for every entry. Legacy entries {pid: qty} contribute their
    int directly; new entries {pid: {qty, branch_id}} contribute `qty`. Safe
    for both shapes so badge counts never blow up on a value that's actually a
    dict.
    """
    if not cart:
        return 0
    total = 0
    for entry in cart.values():
        if isinstance(entry, dict):
            total += int(entry.get("qty", 0) or 0)
        else:
            total += int(entry or 0)
    return total


def _cart_summary_json(cart: dict, touched_pid=None) -> dict:
    """Build the JSON payload returned by cart/update and cart/remove.

    Includes:
      • `ok` / `cart_count` — for the topbar badge.
      • `empty`             — `True` when the last item was just removed.
      • `grand_total`       — discount-aware, mirrors what the page's
                             summary card shows.
      • `product_id` / `quantity` / `line_total`
                           — convenience echo of the row that was just
                             touched. Optional: skips when the client
                             doesn't need to patch a single row
                             (e.g. right after a full page load).
      • `items`             — one entry per remaining product so the
                             client can rerender each row's subtotal
                             and the "+/−" max without re-fetching.

    Handle both cart shapes: legacy {pid: qty} and
    {pid: {"qty": n, "branch_id": bid}}.
    """
    cart_count = _cart_qty_sum(cart)
    grand_total = 0.0
    items_out = []

    if not cart:
        return {
            "ok": True,
            "empty": True,
            "cart_count": 0,
            "grand_total": 0.0,
            "items": [],
        }

    rows = query(
        "SELECT product_id, unit_price, cat_id FROM product "
        "WHERE product_id = ANY(%s)",
        (list(cart.keys()),),
    )
    by_product, by_cat = _get_active_discounts()
    unit_prices = {r["product_id"]: float(r["unit_price"]) for r in rows}

    touched_line = None

    for pid, entry in cart.items():
        qty = entry["qty"] if isinstance(entry, dict) else int(entry or 0)
        if not qty:
            continue
        unit = unit_prices.get(pid)
        if unit is None:
            # Product disappeared (deleted/deactivated) — keep the cart
            # consistent by dropping the orphan entry, don't bill a phantom.
            continue
        cat_id = next((r["cat_id"] for r in rows if r["product_id"] == pid), None)
        disc_price, _ = _apply_discount(unit, pid, cat_id, by_product, by_cat)
        line_total = disc_price * qty
        grand_total += line_total
        items_out.append({
            "product_id": pid,
            "quantity": qty,
            "unit_price": unit,
            "disc_price": disc_price,
            "line_total": line_total,
        })
        if touched_pid is not None and str(pid) == str(touched_pid):
            touched_line = {
                "product_id": pid,
                "quantity": qty,
                "line_total": line_total,
            }

    payload = {
        "ok": True,
        "empty": False,
        "cart_count": cart_count,
        "grand_total": grand_total,
        "items": items_out,
    }
    if touched_line is not None:
        payload["product_id"] = touched_line["product_id"]
        payload["quantity"]   = touched_line["quantity"]
        payload["line_total"] = touched_line["line_total"]
    return payload

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

    # ── Stock availability pre-check ───────────────────────────────
    # Two customers can race on the same SKU.  Before we charge anyone
    # (or even create a sale row / payment row / online_order row),
    # read the *live* branch_inventory for every cart line.  If a
    # product is INACTIVE (deactivated by the admin/manager) or the
    # branch stock is below the requested quantity, abort with a
    # structured 409 — no inserts, no stock decrement, no payment.
    stock_rows = query("""
        SELECT bi.product_id, bi.quantity,
               COALESCE(p.is_active, 'N') AS is_active,
               p.product_name
        FROM   branch_inventory bi
        JOIN   product p USING (product_id)
        WHERE  bi.branch_id = %s
          AND  bi.product_id = ANY(%s)
    """, (branch_id, list(cart.keys())))

    stock_by_pid = {r["product_id"]: r for r in stock_rows}

    unavailable = []
    for pid, qty, _bid in _cart_iter(cart):
        if qty <= 0:
            continue
        row = stock_by_pid.get(pid)
        # No row at all = product isn't stocked at this branch
        if row is None or (row.get("is_active") or "N") != "Y":
            unavailable.append({
                "product_id": pid,
                "product_name": row["product_name"] if row else pid,
                "requested": qty,
                "available": 0,
                "reason": "inactive",
            })
            continue
        avail = int(float(row["quantity"] or 0))
        if avail <= 0:
            unavailable.append({
                "product_id": pid,
                "product_name": row["product_name"],
                "requested": qty,
                "available": avail,
                "reason": "out_of_stock",
            })
        elif avail < qty:
            unavailable.append({
                "product_id": pid,
                "product_name": row["product_name"],
                "requested": qty,
                "available": avail,
                "reason": "insufficient_stock",
            })

    if unavailable:
        # Always return JSON so the checkout page can render a modal
        # listing exactly which items are unavailable.  If the client
        # somehow bypassed fetch (rare), they'll see the JSON in the
        # browser — still no DB writes happened.
        return JSONResponse(
            {"ok": False, "reason": "stock_unavailable",
             "unavailable": unavailable,
             "redirect": "/customer/cart"},
            status_code=409,
        )

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
        qty = _cart_qty(cart, pid)
        if not qty:
            continue

        disc_price, _ = _apply_discount(p["unit_price"], pid, p["cat_id"], by_product, by_cat)
        original_unit = float(p["unit_price"])
        original_line = original_unit * qty
        disc_line = disc_price * qty

        # Mirror the cashier POS data shape so both receipt renderers
        # (cashier bill and branch-manager order bill) see the same fields:
        #   unit_price  = ORIGINAL catalog unit price
        #   line_total  = discounted line total the customer actually pays
        # The `discount_id` column gets the active deal (if any) so the
        # JOIN to `discount` in the bill endpoint can render the badge
        # and recompute the original price when needed.
        disc = by_product.get(pid) or by_cat.get(p["cat_id"])
        disc_id = disc["discount_id"] if disc else None

        subtotal += original_line
        discount_amt += original_line - disc_line
        items.append((pid, qty, original_unit, disc_line, disc_id))

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

    for pid, qty, unit_price, line_total, disc_id in items:
        execute("""
            INSERT INTO sale_item
                (sale_id, product_id, quantity, unit_price, line_total, discount_id)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (sale_id, pid, qty, round(unit_price, 2), round(line_total, 2), disc_id))

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

    # ── Notify the branch manager that a new online order landed ────────
    # Fire-and-forget: a notification failure must never break checkout.
    try:
        cust_row = query(
            "SELECT cust_name FROM customer WHERE cust_id = %s",
            (cust_id,),
        )
        cust_name = cust_row[0]["cust_name"] if cust_row else "A customer"
        # `items` is a list of 5-tuples: (pid, qty, unit_price, line_total, disc_id)
        # — unpack only the fields we need to avoid `not enough values to unpack`.
        item_count = sum(qty for _, qty, *_ in items)
        notify_branch_manager(
            branch_id,
            "NEW_ONLINE_ORDER",
            "New online order",
            f"{cust_name} placed order {order_id} — {item_count} item(s), "
            f"BDT {total_amt:,.2f} via {payment_method}.",
            link_url="/employee/branch/orders",
            ref_table="online_order",
            ref_id=order_id,
        )
    except Exception as _notif_err:
        # Never let a notifier bug roll back a successful checkout.
        print(f"[notify] NEW_ONLINE_ORDER failed: {_notif_err}")

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

    cart = request.session.get("cart", {})
    # A cart "has items" only when at least one entry actually has a
    # positive qty.  Stale dicts with qty=0 (from cancel/update flows
    # or partial migrations) MUST NOT lock the page, otherwise the
    # branch pill stays disabled even when the cart is functionally
    # empty and the customer is stuck on a branch.
    cart_has_items = any(q > 0 for _, q, _ in _cart_iter(cart))
    # ── Single source of truth ─────────────────────────────
    # The cart is the ground truth for which branch the customer is
    # shopping.  Each cart entry stores the branch the product came
    # from, so even if the session["selected_branch"] key drifts or
    # was never set, the page below will render the EXACT branch the
    # cart was built against (banner ↔ pill ↔ products agree).
    cart_branch_id = _cart_locked_branch(cart)

    default_branch = next((b for b in branches if "dhanmondi" in b["branch_name"].lower()), branches[0] if branches else None)
    session_branch_id = request.session.get("selected_branch")
    if not session_branch_id and default_branch:
        session_branch_id = default_branch["branch_id"]
        request.session["selected_branch"] = session_branch_id

    # Pick the branch in this priority order:
    #   1. cart-derived branch (when cart has items)
    #   2. session["selected_branch"] (when cart is empty)
    #   3. fallback to the active default
    if cart_has_items and cart_branch_id:
        selected_branch_id = cart_branch_id
        # Re-sync the session key so future POSTs (e.g. add-to-cart from
        # this page) use the locked branch, not a stale one.
        if session_branch_id != cart_branch_id:
            request.session["selected_branch"] = cart_branch_id
    else:
        selected_branch_id = session_branch_id

    selected_branch = next((b for b in branches if b["branch_id"] == selected_branch_id), None)

    # ── Single source of truth ─────────────────────────────────
    # The branch dropdown posts to /customer/cart/set-branch (same as
    # storefront.html).  But a user could still hit
    # /customer/shop?branch=X directly to try to bypass the cart-lock
    # guard.  If the cart is non-empty, ignore the query string and
    # force the page to use whatever branch the cart was already
    # locked to.  The locked-banner on the page will explain why.
    if cart_has_items and selected_branch_id:
        # Lock the page to the cart's branch, regardless of ?branch=
        pass  # selected_branch_id already comes from cart/session above
    elif request.query_params.get("branch") and not cart_has_items:
        # Only honour the query-string when the cart is empty.
        candidate = request.query_params["branch"].strip()
        if any(b["branch_id"] == candidate for b in branches):
            request.session["selected_branch"] = candidate
            selected_branch_id = candidate
            selected_branch = next((b for b in branches if b["branch_id"] == candidate), None)

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
    filtered_products = []
    for p in raw_products:
        if selected_cat_id is not None:
            in_filter = (p["cat_id"] and p["cat_id"].upper() == selected_cat_id.upper()) \
                        or (p["cat_id"] and p["cat_id"].upper() in {x.upper() for x in extra_cat_ids})
            if not in_filter:
                continue
        disc_price, disc_label = _apply_discount(p["unit_price"], p["product_id"], p["cat_id"], by_product, by_cat)
        p["image_url"] = _normalize_image_url(p.get("image_url"))
        filtered_products.append({**p, "disc_price": disc_price, "disc_label": disc_label})

    # ── Pagination ────────────────────────────────────────────────
    # 20 cards per page; preserves ?cat=, ?q=, ?branch= across pages
    # by appending/rewriting only the `page` query param.
    PAGE_SIZE = 20
    total_products = len(filtered_products)
    total_pages   = max(1, (total_products + PAGE_SIZE - 1) // PAGE_SIZE)

    try:
        current_page = int(request.query_params.get("page", "1"))
    except (TypeError, ValueError):
        current_page = 1
    current_page = max(1, min(current_page, total_pages))

    start = (current_page - 1) * PAGE_SIZE
    end   = start + PAGE_SIZE
    products = filtered_products[start:end]

    return templates.TemplateResponse(request, "customer/shop.html", {
        "products": products,
        "branches": branches,
        "selected_branch": selected_branch,
        "categories": categories,
        "selected_cat_id": selected_cat_id,
        "selected_cat_name": selected_cat_name,
        "cart_locked": cart_has_items,
        # ── Locked-cart banner context (cart-as-truth) ─────────────
        "locked_branch_name": selected_branch["branch_name"] if selected_branch else None,
        "locked_cart_items": sum((e[1] for e in _cart_iter(cart))),
        "locked_cart_total": _cart_total(cart),
        # ── Pagination context ────────────────────────────────
        "current_page":   current_page,
        "total_pages":    total_pages,
        "total_products": total_products,
        "page_size":      PAGE_SIZE,
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

    # ── Branch availability guard ────────────────────────────────────────
    # If the customer already locked a branch in the session, reject adds
    # for products that aren't stocked at that branch.  Mirrors the storefront
    # "Not available in this branch" badge so direct API POSTs can't smuggle
    # in items the customer already saw as unavailable.
    _sel_branch = request.session.get("selected_branch")
    if _sel_branch:
        _inv_row = query(
            """
            SELECT  bi.quantity,
                    p.product_name,
                    COALESCE(p.is_active, 'N') AS is_active
            FROM    branch_inventory bi
            JOIN    product         p  USING (product_id)
            WHERE   bi.branch_id  = %s
              AND   bi.product_id = %s
            """,
            (_sel_branch, product_id),
        )
        _inv_qty     = int((_inv_row[0] or {}).get("quantity") or 0) if _inv_row else 0
        _prod_name   = ((_inv_row[0] or {}).get("product_name") or product_id) if _inv_row else product_id
        _is_active   = ((_inv_row[0] or {}).get("is_active") or "N") if _inv_row else "N"
        if not _inv_row or _inv_qty <= 0 or _is_active != "Y":
            if "application/json" in content_type:
                return JSONResponse(
                    {
                        "ok":           False,
                        "reason":       "not_in_branch",
                        "product_id":   product_id,
                        "product_name": _prod_name,
                        "branch_id":    _sel_branch,
                        "available":    _inv_qty,
                    },
                    status_code=409,
                )
            # Non-JSON submission → bounce back to storefront so the user sees
            # the unavailable badge rather than landing on the shop page.
            return RedirectResponse("/", status_code=302)

    # ── Update the session cart ──────────────────────────────────────────
    # Each cart entry is now {qty, branch_id} so the cart itself is the
    # ground truth for which branch the customer is shopping.  This makes
    # it impossible for the banner / pill / products query to disagree,
    # because every read of the locked branch comes from the cart.
    cart = request.session.get("cart", {})
    add_branch_id = request.session.get("selected_branch")

    existing = cart.get(product_id)
    if isinstance(existing, dict):
        prev_qty = int(existing.get("qty", 0))
    elif isinstance(existing, (int, float)):
        prev_qty = int(existing)        # legacy shape {pid: qty}
    else:
        prev_qty = 0
    cart[product_id] = {
        "qty": prev_qty + quantity,
        "branch_id": add_branch_id,
    }
    request.session["cart"] = cart

    cart_count = sum((e[1] for e in _cart_iter(cart)))

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
            "qty": cart[product_id]["qty"] if isinstance(cart[product_id], dict) else cart[product_id],
            "cart_count": cart_count,
        })

    # ── Classic form fallback ────────────────────────────────────────────
    return RedirectResponse("/customer/shop?msg=added", status_code=302)


@customer_router.post("/cart/set-branch")
async def set_cart_branch(request: Request, session=Depends(require_customer)):
    """
    Persist the branch the customer picked from the storefront popup.

    The storefront calls this once, the first time the user clicks an
    inline "add to cart" button.  After that the chosen branch sticks to
    the session and every subsequent add-to-cart just goes through.
    """
    content_type = (request.headers.get("content-type") or "").lower()
    if "application/json" in content_type:
        try:
            payload = await request.json()
        except Exception:
            payload = {}
        branch_id = (payload.get("branch_id") or "").strip()
    else:
        form = await request.form()
        branch_id = (form.get("branch_id") or "").strip()

    if not branch_id:
        if "application/json" in content_type:
            return JSONResponse({"ok": False, "error": "Missing branch_id"}, status_code=400)
        return RedirectResponse("/", status_code=302)

    # Validate that the branch exists & is active
    row = query(
        "SELECT branch_id, branch_name FROM branch "
        "WHERE branch_id = %s AND is_active = 'Y'",
        (branch_id,),
    )
    if not row:
        if "application/json" in content_type:
            return JSONResponse({"ok": False, "error": "Invalid branch"}, status_code=400)
        return RedirectResponse("/", status_code=302)

    request.session["selected_branch"] = branch_id

    if "application/json" in content_type:
        return JSONResponse({
            "ok": True,
            "branch_id":   branch_id,
            "branch_name": row[0]["branch_name"],
        })
    return RedirectResponse(request.headers.get("referer") or "/", status_code=302)


# ══════════════════════════════════════════════════════════════════════════════
#  STOREFRONT AVAILABILITY FEED
#
#  Returns a JSON snapshot of which active products are in stock at the
#  given branch.  The storefront uses this on the client side to re-tag
#  every product card after the customer picks (or switches) a branch, so
#  the "Not available in this branch" badge appears immediately without a
#  full page refresh.
# ══════════════════════════════════════════════════════════════════════════════
@customer_router.get("/storefront/availability")
def storefront_availability(request: Request, branch_id: str = "", session=Depends(require_customer)):
    branch_id = (branch_id or "").strip()
    if not branch_id:
        return JSONResponse({"ok": False, "error": "Missing branch_id"}, status_code=400)

    branch_row = query(
        "SELECT branch_id, branch_name FROM branch "
        "WHERE branch_id = %s AND is_active = 'Y'",
        (branch_id,),
    )
    if not branch_row:
        return JSONResponse({"ok": False, "error": "Invalid branch"}, status_code=400)

    rows = query(
        """
        SELECT  p.product_id,
                COALESCE(bi.quantity, 0) AS quantity,
                COALESCE(p.is_active, 'N') AS is_active
        FROM    product          p
        LEFT    JOIN branch_inventory bi
                ON  bi.product_id = p.product_id
                AND bi.branch_id  = %s
        WHERE   p.is_active = 'Y'
        ORDER   BY p.product_name
        """,
        (branch_id,),
    ) or []

    availability = [
        {
            "product_id": r["product_id"],
            "available":  (int(r.get("quantity") or 0) > 0)
                          and ((r.get("is_active") or "N") == "Y"),
            "quantity":   int(r.get("quantity") or 0),
        }
        for r in rows
    ]

    return JSONResponse({
        "ok":           True,
        "branch_id":    branch_id,
        "branch_name":  branch_row[0]["branch_name"],
        "availability": availability,
    })




@customer_router.get("/cart", response_class=HTMLResponse)
def view_cart(request: Request, session=Depends(require_customer)):
    cart = request.session.get("cart", {})
    items = []
    grand_total = 0.0
    total_savings = 0.0

    if cart:
        raw_products = query("""
            SELECT product_id, product_name, brand, unit_price, unit, cat_id, image_url
            FROM product
            WHERE product_id = ANY(%s)
        """, (list(cart.keys()),))

        # Pull per-branch stock so the cart page can clamp its "+"
        # buttons the same way the shop grid does.  We use the branch
        # each cart line was actually created against (the cart's own
        # branch_id) — falling back to the session's selected branch.
        cart_branch_map = {}
        for pid, entry in cart.items():
            if isinstance(entry, dict):
                cart_branch_map[pid] = entry.get("branch_id")
        fallback_branch = request.session.get("selected_branch")

        branch_ids = sorted({b for b in cart_branch_map.values() if b} | ({fallback_branch} if fallback_branch else set()))
        stock_by_pid = {}
        if branch_ids:
            for pid in cart.keys():
                bid = cart_branch_map.get(pid) or fallback_branch
                if not bid:
                    continue
                row = query(
                    "SELECT quantity FROM branch_inventory "
                    "WHERE branch_id = %s AND product_id = %s",
                    (bid, pid),
                )
                if row:
                    stock_by_pid[pid] = int(row[0]["quantity"])

        by_product, by_cat = _get_active_discounts()

        for p in raw_products:
            qty = _cart_qty(cart, p["product_id"])
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
                "original_price": float(p["unit_price"]),
                # Same normalization the shop page uses so emoji fallback
                # only kicks in when the product genuinely has no image.
                "image_url": _normalize_image_url(p.get("image_url")),
                # Available stock at the line's branch — `None` when the
                # product isn't tracked there, in which case the cart UI
                # falls back to a generous cap (99) instead of locking up.
                "stock": stock_by_pid.get(p["product_id"]),
            })

    return templates.TemplateResponse(request, "customer/cart.html", {
        "items": items,
        "grand_total": grand_total,
        "total_savings": total_savings,
        **_customer_context(request, session),
    })



@customer_router.post("/cart/update")
async def update_cart(
    request: Request,
    session=Depends(require_customer)
):
    """Update a cart line's quantity.

    Accepts either a regular form POST (no JS) or a JSON POST from
    `fetch`.  The JSON response lets the cart page rerender the row
    + summary + navbar badge in place instead of doing a full reload.
    """
    content_type = (request.headers.get("content-type") or "").lower()
    wants_json = "application/json" in content_type or \
                 request.headers.get("x-requested-with") == "fetch"

    if "application/json" in content_type:
        try:
            payload = await request.json()
        except Exception:
            payload = {}
        product_id = (payload.get("product_id") or "").strip()
        try:
            quantity = int(payload.get("quantity") or 0)
        except (TypeError, ValueError):
            quantity = 0
    else:
        form = await request.form()
        product_id = (form.get("product_id") or "").strip()
        try:
            quantity = int(form.get("quantity") or 0)
        except (TypeError, ValueError):
            quantity = 0

    if not product_id:
        if wants_json:
            return JSONResponse({"ok": False, "error": "Missing product_id"}, status_code=400)
        return RedirectResponse("/customer/cart", status_code=302)

    cart = request.session.get("cart", {})

    if quantity <= 0:
        cart.pop(product_id, None)
    else:
        existing = cart.get(product_id)
        existing_branch = (
            existing.get("branch_id")
            if isinstance(existing, dict)
            else (request.session.get("selected_branch") if existing is not None else None)
        )
        cart[product_id] = {"qty": int(quantity), "branch_id": existing_branch}

    request.session["cart"] = cart

    if wants_json:
        # Re-derive the totals so the client can rerender without a
        # round-trip to GET /cart.  Keeps the badge / summary / row
        # perfectly in sync with the session.
        return JSONResponse(_cart_summary_json(cart, touched_pid=product_id))
    return RedirectResponse("/customer/cart", status_code=302)


@customer_router.post("/cart/remove")
async def remove_from_cart(
    request: Request,
    session=Depends(require_customer)
):
    """Remove a single line from the cart.  Same dual-mode contract as
    `update_cart` so the page can do an in-place slide-out instead of a
    full reload."""
    content_type = (request.headers.get("content-type") or "").lower()
    wants_json = "application/json" in content_type or \
                 request.headers.get("x-requested-with") == "fetch"

    if "application/json" in content_type:
        try:
            payload = await request.json()
        except Exception:
            payload = {}
        product_id = (payload.get("product_id") or "").strip()
    else:
        form = await request.form()
        product_id = (form.get("product_id") or "").strip()

    if not product_id:
        if wants_json:
            return JSONResponse({"ok": False, "error": "Missing product_id"}, status_code=400)
        return RedirectResponse("/customer/cart", status_code=302)

    cart = request.session.get("cart", {})
    cart.pop(product_id, None)
    request.session["cart"] = cart

    if wants_json:
        return JSONResponse(_cart_summary_json(cart))
    return RedirectResponse("/customer/cart", status_code=302)


@customer_router.post("/cart/clear")
async def clear_cart(
    request: Request,
    session=Depends(require_customer)
):
    """Empty the cart.  Dual-mode:

      • JSON POST from the cart page → return JSON summary (empty).
      • Anything else → redirect back to the referer (used by the
        locked-branch banner elsewhere on the site).
    """
    content_type = (request.headers.get("content-type") or "").lower()
    wants_json = "application/json" in content_type or \
                 request.headers.get("x-requested-with") == "fetch"

    request.session["cart"] = {}

    if wants_json:
        # Reuse the existing summary builder — returns the standard
        # `empty: true, cart_count: 0, grand_total: 0, items: []`
        # payload the client expects.
        return JSONResponse(_cart_summary_json({}))

    referer = request.headers.get("referer") or "/customer/cart"
    # Stay on the same site — avoid open-redirect via crafted Referer
    if not referer.startswith("/"):
        referer = "/customer/cart"
    return RedirectResponse(referer, status_code=302)



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
        qty = _cart_qty(cart, p["product_id"])
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

    # Pull the customer's saved phone + address so the form can
    # pre-fill them.  Phone is required for delivery dispatch and
    # most customers don't want to type it again on every order.
    cust_id = session.get("user_id")
    cust_row = query(
        "SELECT phone, address FROM customer WHERE cust_id = %s",
        (cust_id,),
    )
    default_phone   = (cust_row[0].get("phone")   if cust_row else "") or ""
    default_address = (cust_row[0].get("address") if cust_row else "") or ""

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
        "default_phone"  : default_phone,
        "default_address": default_address,
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
    cust_name:    str = Form(...),
    email:        str = Form(""),
    address:      str = Form(""),
    dob:          str = Form(""),
    gender:       str = Form(""),
    confirm_pwd:  str = Form(...),  # re-entered in the confirm-password modal
    session=Depends(require_customer),
):
    cust_id = session.get("user_id")

    # ── 1) Verify the password the user re-typed in the modal ────
    confirm_pwd = (confirm_pwd or "").strip()
    if not confirm_pwd:
        return RedirectResponse(
            "/customer/profile?error=Please+enter+your+password+to+save+changes",
            status_code=302,
        )
    pwd_row = query(
        "SELECT password_hash FROM app_user WHERE role='CUSTOMER' AND ref_id=%s",
        (cust_id,),
    )
    stored_hash = pwd_row[0]["password_hash"] if pwd_row else None
    if not stored_hash or not _verify(confirm_pwd, stored_hash):
        return RedirectResponse(
            "/customer/profile?error=Incorrect+password",
            status_code=302,
        )

    # Normalize / validate
    cust_name = cust_name.strip()
    email     = email.strip() or None
    address   = address.strip() or None
    dob       = dob.strip() or None
    gender    = gender.strip().upper() or None
    if gender and gender not in ("M", "F"):
        gender = None

    if not cust_name:
        return RedirectResponse(
            "/customer/profile?error=Name+is+required",
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

    try:
        execute("""
            UPDATE customer
               SET cust_name = %s,
                   email     = %s,
                   address   = %s,
                   dob       = %s,
                   gender    = %s
             WHERE cust_id = %s
        """, (cust_name, email, address, dob, gender, cust_id))
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
    current_password: str = Form(...),
    session=Depends(require_customer)
):
    cust_id = session.get("user_id")
    current_password = (current_password or "").strip()

    # Verify the user's password before allowing the destructive action.
    pwd_row = query(
        "SELECT password_hash FROM app_user WHERE role='CUSTOMER' AND ref_id=%s",
        (cust_id,),
    )
    stored_hash = pwd_row[0]["password_hash"] if pwd_row else None
    if not stored_hash or not _verify(current_password, stored_hash):
        return RedirectResponse(
            "/customer/profile?error=Password+incorrect.+Delete+was+cancelled",
            status_code=302,
        )

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


@customer_router.post("/profile/password")
def customer_password_update(
    request: Request,
    current_password: str = Form(...),
    new_password:     str = Form(...),
    confirm_password: str = Form(...),
    session=Depends(require_customer),
):
    """Self-service password change for logged-in customers."""
    cust_id = session.get("user_id")

    current_password = current_password.strip()
    new_password     = new_password.strip()
    confirm_password = confirm_password.strip()

    # Match check
    if new_password != confirm_password:
        return RedirectResponse(
            "/customer/profile?error=New+passwords+do+not+match",
            status_code=302,
        )

    # Basic strength check — frontend also enforces this, but server
    # is the source of truth.
    if len(new_password) < 6:
        return RedirectResponse(
            "/customer/profile?error=Password+must+be+at+least+6+characters",
            status_code=302,
        )

    if new_password == current_password:
        return RedirectResponse(
            "/customer/profile?error=New+password+must+differ+from+current",
            status_code=302,
        )

    # Confirm current password is correct
    pwd_row = query(
        "SELECT password_hash FROM app_user WHERE role='CUSTOMER' AND ref_id=%s",
        (cust_id,),
    )
    stored_hash = pwd_row[0]["password_hash"] if pwd_row else None
    if not stored_hash or not _verify(current_password, stored_hash):
        return RedirectResponse(
            "/customer/profile?error=Current+password+is+incorrect",
            status_code=302,
        )

    # Update password hash
    try:
        execute(
            "UPDATE app_user SET password_hash=%s WHERE role='CUSTOMER' AND ref_id=%s",
            (_hash(new_password), cust_id),
        )
    except Exception as e:
        return RedirectResponse(
            f"/customer/profile?error=Could+not+update+password:+{quote(str(e))}",
            status_code=302,
        )

    return RedirectResponse("/customer/profile?msg=password_updated", status_code=302)



@customer_router.get("/dashboard", response_class=HTMLResponse)
def customer_dashboard(request: Request, session=Depends(require_customer)):
    cust_id = session.get("user_id")

    my_orders = query("""
        SELECT s.sale_id,
               TO_CHAR(s.sale_date, 'DD Mon YYYY HH24:MI') AS sale_date,
               b.branch_name, s.total_amt,
               s.payment_status, s.order_type,
               oo.order_id, oo.order_status, oo.delivery_address,
               pay.status  AS pay_status,
               pay.method  AS pay_method
        FROM   sale s
               JOIN branch b ON s.branch_id = b.branch_id
               LEFT JOIN online_order oo ON s.sale_id = oo.sale_id
               LEFT JOIN payment pay      ON pay.sale_id = s.sale_id
        WHERE  s.cust_id = %s
        ORDER BY s.sale_date DESC
        LIMIT  50
    """, (cust_id,))

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


@customer_router.post("/order/cancel/{sale_id}")
def cancel_order(
    sale_id: str,
    session=Depends(require_customer),
):
    """Allow a customer to cancel one of their own orders.

    Mirrors the branch-manager cancel flow but enforces:
      • ownership — the sale must belong to the logged-in customer
      • online order — POS / walk-in sales have no online_order row
      • cancellable state — order_status must still be 'PLACED'

    On success: stock is restocked, loyalty points reversed, payment
    refunded (if already PAID), and the sale is marked CANCELLED.
    """
    cust_id = session.get("user_id")

    owned = query("""
        SELECT  oo.order_id, oo.order_status, s.cust_id
        FROM    online_order oo
        JOIN    sale s ON s.sale_id = oo.sale_id
        WHERE   oo.sale_id = %s
          AND   s.cust_id = %s
    """, (sale_id, cust_id))

    if not owned:
        return RedirectResponse(
            "/customer/dashboard?error=Order+not+found",
            status_code=302,
        )

    order_id = owned[0]["order_id"]
    current  = (owned[0]["order_status"] or "").upper()

    if current != "PLACED":
        return RedirectResponse(
            f"/customer/dashboard?error=Order+can+only+be+cancelled+while+it+is+still+placed",
            status_code=302,
        )

    # Mark the online_order as CANCELLED so the row drops out of the
    # "active" state on the dashboard (Cancel button → "Cancelled"
    # placeholder) and the manager's order queue stays consistent.
    # Mirrors the branch-manager flow at employee.py:_cancel_and_refund,
    # which also flips online_order.order_status before delegating.
    execute(
        "UPDATE online_order SET order_status = 'CANCELLED' WHERE order_id = %s",
        (order_id,),
    )

    _cancel_and_refund_customer(order_id)

    return RedirectResponse(
        "/customer/dashboard?msg=order_cancelled",
        status_code=302,
    )


# ══════════════════════════════════════════════════════════════════════════════
#  CUSTOMER NOTIFICATIONS — feeds the storefront bell icon
#
#  GET  /customer/notifications
#       Returns the 20 most-recent notifications addressed to the logged-in
#       customer.  Used by the bell widget in storefront.html.
#
#  POST /customer/notifications/{notif_id}/read
#       Marks a single notification as read.  Scoped by recipient_type +
#       recipient_id so a customer can never mutate someone else's row.
#
#  POST /customer/notifications/read-all
#       Marks every unread notification for the current customer as
#       read in one shot.  Returns the number of rows affected so the
#       bell widget can update its badge without a second fetch.
# ══════════════════════════════════════════════════════════════════════════════

@customer_router.get("/notifications")
def customer_notifications(session=Depends(require_customer)):
    cust_id = session.get("user_id")
    rows = query("""
        SELECT notif_id, notif_type, title, message, link_url, is_read,
               TO_CHAR(created_at, 'DD Mon, HH12:MI AM') AS created_at
        FROM   notification
        WHERE  recipient_type = 'CUSTOMER' AND recipient_id = %s
        ORDER  BY created_at DESC
        LIMIT  20
    """, (cust_id,))
    unread = sum(1 for r in rows if r["is_read"] == "N")
    return JSONResponse({"notifications": rows, "unread_count": unread})


@customer_router.post("/notifications/{notif_id}/read")
def customer_mark_notification_read(notif_id: str, session=Depends(require_customer)):
    cust_id = session.get("user_id")
    execute("""
        UPDATE notification SET is_read='Y', read_at=CURRENT_TIMESTAMP
        WHERE  notif_id = %s AND recipient_type='CUSTOMER' AND recipient_id = %s
    """, (notif_id, cust_id))


@customer_router.post("/notifications/read-all")
def customer_mark_all_notifications_read(session=Depends(require_customer)):
    cust_id = session.get("user_id")
    # Snapshot how many are currently unread so the client can show
    # "Marked N as read" without an extra round-trip.
    before = query(
        "SELECT COUNT(*) AS c FROM notification "
        "WHERE recipient_type='CUSTOMER' AND recipient_id=%s AND is_read='N'",
        (cust_id,),
    )
    marked = int(before[0]["c"]) if before else 0
    execute("""
        UPDATE notification SET is_read='Y', read_at=CURRENT_TIMESTAMP
        WHERE  recipient_type='CUSTOMER' AND recipient_id = %s
          AND  is_read = 'N'
    """, (cust_id,))
    return JSONResponse({"marked": marked, "unread_count": 0})