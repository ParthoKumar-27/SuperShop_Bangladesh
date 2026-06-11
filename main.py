from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from database import query, execute

# ── App setup ─────────────────────────────────────────────────
app = FastAPI(
    title="SuperShop Bangladesh",
    description="Multi-branch retail management system",
    version="1.0.0"
)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


# ══════════════════════════════════════════════════════════════
#  HTML PAGE ROUTES  (return rendered HTML)
# ══════════════════════════════════════════════════════════════

@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request):
    # Aggregate stats for the dashboard cards
    stats = {
        "branches":  query("SELECT COUNT(*) AS n FROM branch WHERE is_active='Y'")[0]["n"],
        "products":  query("SELECT COUNT(*) AS n FROM product WHERE is_active='Y'")[0]["n"],
        "customers": query("SELECT COUNT(*) AS n FROM customer")[0]["n"],
        "employees": query("SELECT COUNT(*) AS n FROM employee WHERE is_active='Y'")[0]["n"],
    }
    recent_sales = query("""
        SELECT s.sale_id, b.branch_name,
               COALESCE(c.cust_name, 'Walk-in') AS customer,
               s.total_amt, s.payment_status, s.order_type,
               TO_CHAR(s.sale_date, 'DD Mon YYYY') AS sale_date
        FROM   sale s
               JOIN branch b   ON s.branch_id = b.branch_id
               LEFT JOIN customer c ON s.cust_id = c.cust_id
        ORDER BY s.sale_date DESC
        LIMIT  8
    """)
    return templates.TemplateResponse(
    request,
    "index.html",
    {
        "stats": stats,
        "recent_sales": recent_sales
    }
)


@app.get("/products", response_class=HTMLResponse)
def products_page(request: Request):
    products = query("""
        SELECT p.product_id, p.product_name, p.brand,
               p.unit_price, p.unit, p.is_active,
               c.cat_name, s.supplier_name
        FROM   product p
               LEFT JOIN category c  USING (cat_id)
               LEFT JOIN supplier s  USING (supplier_id)
        ORDER BY p.product_name
    """)
    return templates.TemplateResponse(
    request,
    "products.html",
    {
        "products": products
    }
)


@app.get("/sales", response_class=HTMLResponse)
def sales_page(request: Request):
    sales = query("""
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
        ORDER BY s.sale_date DESC
    """)
    return templates.TemplateResponse(
    request,
    "sales.html",
    {
        "sales": sales
    }
)


@app.get("/customers", response_class=HTMLResponse)
def customers_page(request: Request):
    customers = query("""
        SELECT cust_id, cust_name, email, phone,
               gender, membership_type, loyalty_points,
               TO_CHAR(join_date, 'DD Mon YYYY') AS join_date
        FROM   customer
        ORDER BY cust_name
    """)
    return templates.TemplateResponse(
    request,
    "customers.html",
    {
        "customers": customers
    }
)


@app.get("/branches", response_class=HTMLResponse)
def branches_page(request: Request):
    branches = query("""
        SELECT b.branch_id, b.branch_name, c.city_name,
               b.address, b.phone, b.open_time, b.close_time,
               b.is_active,
               bm.emp_id,
               e.emp_name AS manager_name
        FROM   branch b
               JOIN city c ON b.city_id = c.city_id
               LEFT JOIN branch_manager bm USING (branch_id)
               LEFT JOIN employee e ON bm.emp_id = e.emp_id
        ORDER BY b.branch_id
    """)
    return templates.TemplateResponse(
    request,
    "branches.html",
    {
        "branches": branches
    }
)


@app.get("/inventory", response_class=HTMLResponse)
def inventory_page(request: Request):
    inventory = query("""
        SELECT bi.inv_id, b.branch_name, p.product_name,
               bi.quantity, bi.reorder_level, bi.shelf_location,
               TO_CHAR(bi.last_restocked, 'DD Mon YYYY') AS last_restocked,
               CASE WHEN bi.quantity <= bi.reorder_level
                    THEN 'LOW' ELSE 'OK' END AS stock_status
        FROM   branch_inventory bi
               JOIN branch  b USING (branch_id)
               JOIN product p USING (product_id)
        ORDER BY stock_status DESC, b.branch_name
    """)
    return templates.TemplateResponse(
    request,
    "base.html", #temporary until we make inventory.html
    {
        "inventory": inventory
    }
)


# ══════════════════════════════════════════════════════════════
#  JSON API ROUTES  (used by /docs and AJAX calls)
#  Visit http://localhost:8000/docs to see all of these
# ══════════════════════════════════════════════════════════════

@app.get("/api/products", tags=["Products"])
def api_products():
    return query("""
        SELECT p.product_id, p.product_name, p.brand,
               p.unit_price, p.unit, c.cat_name
        FROM   product p JOIN category c USING (cat_id)
        WHERE  p.is_active = 'Y'
        ORDER BY p.product_name
    """)

@app.get("/api/customers", tags=["Customers"])
def api_customers():
    return query("SELECT * FROM customer ORDER BY cust_name")

@app.get("/api/sales", tags=["Sales"])
def api_sales():
    return query("""
        SELECT s.*, b.branch_name, COALESCE(c.cust_name,'Walk-in') AS cust_name
        FROM   sale s
               JOIN branch b ON s.branch_id = b.branch_id
               LEFT JOIN customer c ON s.cust_id = c.cust_id
        ORDER BY sale_date DESC
    """)

@app.get("/api/branches", tags=["Branches"])
def api_branches():
    return query("""
        SELECT b.*, c.city_name
        FROM   branch b JOIN city c USING (city_id)
    """)

@app.get("/api/inventory/low-stock", tags=["Inventory"])
def api_low_stock():
    """Products where quantity is at or below reorder level."""
    return query("""
        SELECT b.branch_name, p.product_name,
               bi.quantity, bi.reorder_level
        FROM   branch_inventory bi
               JOIN branch  b USING (branch_id)
               JOIN product p USING (product_id)
        WHERE  bi.quantity <= bi.reorder_level
        ORDER BY b.branch_name
    """)

@app.get("/api/sales/by-branch", tags=["Sales"])
def api_sales_by_branch():
    """Total revenue per branch."""
    return query("""
        SELECT b.branch_name,
               COUNT(s.sale_id)  AS total_sales,
               SUM(s.total_amt)  AS total_revenue,
               AVG(s.total_amt)  AS avg_sale
        FROM   sale s JOIN branch b USING (branch_id)
        WHERE  s.payment_status = 'PAID'
        GROUP BY b.branch_name
        ORDER BY total_revenue DESC
    """)

@app.get("/api/customers/{cust_id}", tags=["Customers"])
def api_customer_detail(cust_id: str):
    """Get one customer plus their sales history."""
    customer = query(
        "SELECT * FROM customer WHERE cust_id = %s", (cust_id,)
    )
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    orders = query("""
        SELECT sale_id, sale_date, total_amt, payment_status, order_type
        FROM   sale
        WHERE  cust_id = %s
        ORDER BY sale_date DESC
    """, (cust_id,))
    return {"customer": customer[0], "orders": orders}


# ══════════════════════════════════════════════════════════════
#  UPDATE / DELETE ROUTES
# ══════════════════════════════════════════════════════════════

@app.post("/customers/{cust_id}/update-membership", tags=["Customers"])
def update_membership(cust_id: str, membership_type: str = Form(...)):
    execute(
        "UPDATE customer SET membership_type = %s WHERE cust_id = %s",
        (membership_type, cust_id)
    )
    return RedirectResponse("/customers", status_code=302)

@app.post("/products/{product_id}/deactivate", tags=["Products"])
def deactivate_product(product_id: str):
    execute(
        "UPDATE product SET is_active = 'N' WHERE product_id = %s",
        (product_id,)
    )
    return {"message": f"{product_id} deactivated"}