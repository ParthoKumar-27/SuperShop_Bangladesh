from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.templating import Jinja2Templates
from urllib.parse import quote
from database import query, execute
from auth import require_customer
from fastapi import FastAPI, Request, Form, HTTPException, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware


customer_router = APIRouter(prefix="/customer", tags=["Customer"])
templates = Jinja2Templates(directory="templates")
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



@customer_router.get("/invoice/{sale_id}", response_class=HTMLResponse)
def view_invoice(sale_id: str, request: Request, session=Depends(require_customer)):
    cust_id = session.get("user_id")

    # Verify that this sale record actually belongs to the requesting customer
    sale_data = query("""
        SELECT s.sale_id, TO_CHAR(s.sale_date, 'DD Mon YYYY HH24:MI') AS sale_date,
               s.subtotal, s.discount_amt, s.tax_amt, s.total_amt, s.payment_status,
               b.branch_name, b.address AS branch_address, b.phone AS branch_phone
        FROM sale s
        JOIN branch b ON s.branch_id = b.branch_id
        WHERE s.sale_id = %s AND s.cust_id = %s
    """, (sale_id, cust_id))

    if not sale_data:
        raise HTTPException(status_code=404, detail="Invoice record not found")

    # Fetch corresponding individual checkout line items
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

@customer_router.post("/checkout")
def place_order(
    request: Request,
    branch_id: str = Form(...),
    payment_method: str = Form(...),
    session=Depends(require_customer)
):
    cart = request.session.get("cart", {})
    if not cart:
        return RedirectResponse("/customer/shop", status_code=302)

    cust_id = session.get("user_id")

    # 1. Get current prices for items in cart
    products = query("""
        SELECT product_id, unit_price
        FROM product
        WHERE product_id = ANY(%s) AND is_active = 'Y'
    """, (list(cart.keys()),))
    price_map = {p["product_id"]: float(p["unit_price"]) for p in products}

    items = []
    subtotal = 0.0
    for pid, qty in cart.items():
        if pid not in price_map:
            continue
        line_total = price_map[pid] * qty
        subtotal += line_total
        items.append((pid, qty, price_map[pid], line_total))

    if not items:
        return RedirectResponse("/customer/shop", status_code=302)

    discount_amt = 0.0
    tax_amt = 0.0
    total_amt = subtotal - discount_amt + tax_amt
    payment_status = "PENDING" if payment_method == "CASH" else "PAID"

    # 2. Find an employee at the chosen branch to attribute the sale to
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

    # 3. Generate IDs
    sale_id = _next_id("S-", "sale", "sale_id", 8)
    order_id = _next_id("O-", "online_order", "order_id", 8)

    # 4. Insert sale
    execute("""
        INSERT INTO sale
            (sale_id, branch_id, cust_id, emp_id, order_type,
             subtotal, discount_amt, tax_amt, total_amt, payment_status)
        VALUES (%s, %s, %s, %s, 'ONLINE', %s, %s, %s, %s, %s)
    """, (sale_id, branch_id, cust_id, emp_id, subtotal, discount_amt, tax_amt, total_amt, payment_status))

    # 5. Insert sale items
    for pid, qty, unit_price, line_total in items:
        execute("""
            INSERT INTO sale_item (sale_id, product_id, quantity, unit_price, line_total)
            VALUES (%s, %s, %s, %s, %s)
        """, (sale_id, pid, qty, unit_price, line_total))

    # 6. Insert online_order (delivery_address is NOT NULL, so use a placeholder
    #    since this UI is "pickup" style and doesn't collect an address)
    execute("""
        INSERT INTO online_order
            (order_id, cust_id, branch_id, sale_id, order_status, delivery_address)
        VALUES (%s, %s, %s, %s, 'PLACED', %s)
    """, (order_id, cust_id, branch_id, sale_id, f"Self pickup - branch {branch_id}"))

    # 7. Record payment (only for instant methods; CASH is collected on delivery)
    if payment_method != "CASH":
        payment_id = _next_id("PAY-", "payment", "payment_id", 8)
        execute("""
            INSERT INTO payment (payment_id, sale_id, amount, method, status)
            VALUES (%s, %s, %s, %s, 'SUCCESS')
        """, (payment_id, sale_id, total_amt, payment_method))

    # 8. Clear cart
    request.session["cart"] = {}

    return RedirectResponse("/customer/dashboard?msg=order_placed", status_code=302)


@customer_router.get("/shop", response_class=HTMLResponse)
def customer_shop(request: Request, session=Depends(require_customer)):
    products = query("""
        SELECT product_id, product_name, brand, unit_price, unit
        FROM product
        WHERE is_active = 'Y'
        ORDER BY product_name
    """)

    return templates.TemplateResponse(request, "customer/shop.html", {
        "products": products,
        "role": "CUSTOMER",
        "user_name": session.get("user_name"),
    })


@customer_router.post("/cart/add")
def add_to_cart(
    request: Request,
    product_id: str = Form(...),
    quantity: int = Form(1),
    session=Depends(require_customer)
):
    cart = request.session.get("cart", {})
    cart[product_id] = cart.get(product_id, 0) + max(1, quantity)
    request.session["cart"] = cart

    return RedirectResponse("/customer/shop?msg=added", status_code=302)


@customer_router.get("/cart", response_class=HTMLResponse)
def view_cart(request: Request, session=Depends(require_customer)):
    cart = request.session.get("cart", {})

    items = []
    grand_total = 0.0

    if cart:
        products = query("""
            SELECT product_id, product_name, brand, unit_price, unit
            FROM product
            WHERE product_id = ANY(%s)
        """, (list(cart.keys()),))

        for p in products:
            qty = cart.get(p["product_id"], 0)
            line_total = float(p["unit_price"]) * qty
            grand_total += line_total
            items.append({**p, "quantity": qty, "line_total": line_total})

    return templates.TemplateResponse(request, "customer/cart.html", {
        "items": items,
        "grand_total": grand_total,
        "role": "CUSTOMER",
        "user_name": session.get("user_name"),
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

    products = query("""
        SELECT product_id, product_name, brand, unit_price, unit
        FROM product
        WHERE product_id = ANY(%s)
    """, (list(cart.keys()),))

    items = []
    grand_total = 0.0
    for p in products:
        qty = cart.get(p["product_id"], 0)


        line_total = float(p["unit_price"]) * qty
        grand_total += line_total
        items.append({**p, "quantity": qty, "line_total": line_total})

    branches = query("""
        SELECT branch_id, branch_name
        FROM branch
        WHERE is_active = 'Y'
        ORDER BY branch_name
    """)

    return templates.TemplateResponse(request, "customer/checkout.html", {
        "items": items,
        "grand_total": grand_total,
        "branches": branches,
        "role": "CUSTOMER",
        "user_name": session.get("user_name"),
    })


# POST /customer/checkout (place order) comes in the next step —
# it needs to know the exact columns of sale, sale_item, and online_order.
@customer_router.get("/inventory", response_class=HTMLResponse)
def customer_inventory(
    request: Request,
    session=Depends(require_customer)
):
    inventory = query("""
        SELECT
            b.branch_name,
            p.product_name,
            bi.quantity,
            CASE
                WHEN bi.quantity <= bi.reorder_level
                THEN 'LOW'
                ELSE 'AVAILABLE'
            END AS stock_status
        FROM branch_inventory bi
        JOIN branch b USING(branch_id)
        JOIN product p USING(product_id)
        ORDER BY b.branch_name, p.product_name
    """)

    return templates.TemplateResponse(
        request,
        "customer/inventory.html",
        {
            "inventory": inventory,
            "role": "CUSTOMER",
            "user_name": session.get("user_name")
        }
    )

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
            "role": "CUSTOMER",
            "user_name": session.get("user_name")
        }
    )


@customer_router.post("/delete-account")
def delete_customer_account(
    request: Request,
    session=Depends(require_customer)
):
    cust_id = session.get("user_id")

    # Delete customer account
    execute("""
        DELETE FROM customer
        WHERE cust_id = %s
    """, (cust_id,))

    # Clear session
    request.session.clear()

    return RedirectResponse(
        "/?msg=account_deleted",
        status_code=302
    )

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

    cust_info = query(
        "SELECT cust_name, loyalty_points, membership_type FROM customer WHERE cust_id = %s",
        (cust_id,)
    )

    return templates.TemplateResponse(request, "customer/dashboard.html", {
        "my_orders":      my_orders,
        "user_name":      session.get("user_name"),
        "membership":     session.get("membership"),
        "loyalty_points": session.get("loyalty_points"),
        "role":           "CUSTOMER",
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
