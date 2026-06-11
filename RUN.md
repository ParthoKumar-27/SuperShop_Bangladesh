# SuperShop Bangladesh — FastAPI + Tailwind CSS
## Complete Beginner Guide (VS Code + Railway Deployment)

---

## 1. INSTALL THESE FIRST (one time only)

- Python 3.11+ → https://python.org/downloads
- VS Code      → https://code.visualstudio.com
- Git          → https://git-scm.com

### VS Code Extensions to install
Open VS Code → press Ctrl+Shift+X → search and install:
- Python (by Microsoft)
- Pylance (by Microsoft)
- Thunder Client   ← test your API without Postman
- HTML CSS Support
- Auto Rename Tag
- Prettier – Code formatter
- GitLens

---

## 2. FOLDER STRUCTURE

Create a folder called `supershop-web` anywhere on your PC.
Inside it, create exactly this layout:

```
supershop-web/
│
├── main.py              ← FastAPI app (all backend code)
├── database.py          ← PostgreSQL connection helper
├── requirements.txt     ← Python packages
├── Procfile             ← tells Railway how to start the app
├── .env                 ← your secret DB password (never upload)
├── .gitignore           ← files Git should ignore
│
├── templates/           ← HTML pages (Jinja2)
│   ├── base.html        ← shared navbar + layout
│   ├── index.html       ← dashboard / home
│   ├── products.html
│   ├── sales.html
│   ├── customers.html
│   └── branches.html
│
└── static/
    └── js/
        └── utils.js     ← shared JS helpers
```

Open this folder in VS Code:
File → Open Folder → select supershop-web

---

## 3. FILE CONTENTS (copy each one exactly)

---

### requirements.txt

```
fastapi
uvicorn
psycopg2-binary
python-dotenv
jinja2
aiofiles
```

---

### .gitignore

```
.env
__pycache__/
*.pyc
.venv/
venv/
```

---

### .env  (replace with YOUR actual PostgreSQL credentials)

```
DATABASE_URL=postgresql://postgres:yourpassword@localhost:5432/supershop
```

When deployed on Railway, you delete this line and Railway injects
DATABASE_URL automatically.

---

### Procfile

```
web: uvicorn main:app --host 0.0.0.0 --port $PORT
```

---

### database.py

```python
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()  # reads .env file

def get_connection():
    """Return a fresh PostgreSQL connection."""
    return psycopg2.connect(os.getenv("DATABASE_URL"))

def query(sql: str, params=None):
    """
    Run a SELECT query and return a list of dicts.
    Example:
        rows = query("SELECT * FROM product WHERE is_active = %s", ('Y',))
    """
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute(sql, params or ())
    cols = [desc[0] for desc in cur.description]
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [dict(zip(cols, row)) for row in rows]

def execute(sql: str, params=None):
    """
    Run INSERT / UPDATE / DELETE.
    Example:
        execute("UPDATE customer SET loyalty_points = %s WHERE cust_id = %s", (500, 'C-00001'))
    """
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute(sql, params or ())
    conn.commit()
    cur.close()
    conn.close()
```

---

### main.py

```python
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
    return templates.TemplateResponse("index.html", {
        "request": request,
        "stats": stats,
        "recent_sales": recent_sales
    })


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
    return templates.TemplateResponse("products.html", {
        "request": request, "products": products
    })


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
    return templates.TemplateResponse("sales.html", {
        "request": request, "sales": sales
    })


@app.get("/customers", response_class=HTMLResponse)
def customers_page(request: Request):
    customers = query("""
        SELECT cust_id, cust_name, email, phone,
               gender, membership_type, loyalty_points,
               TO_CHAR(join_date, 'DD Mon YYYY') AS join_date
        FROM   customer
        ORDER BY cust_name
    """)
    return templates.TemplateResponse("customers.html", {
        "request": request, "customers": customers
    })


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
    return templates.TemplateResponse("branches.html", {
        "request": request, "branches": branches
    })


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
    return templates.TemplateResponse("inventory.html", {
        "request": request, "inventory": inventory
    })


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
```

---

### templates/base.html  (shared layout for all pages)

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>SuperShop BD – {% block title %}{% endblock %}</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <script>
    tailwind.config = {
      theme: {
        extend: {
          colors: {
            brand: { DEFAULT: '#1e3a5f', light: '#2563eb' }
          }
        }
      }
    }
  </script>
</head>
<body class="bg-gray-100 min-h-screen">

  <!-- ── NAVBAR ── -->
  <nav class="bg-gray-900 text-white px-6 py-3 flex items-center justify-between shadow-lg">
    <a href="/" class="text-xl font-bold tracking-wide">
      🛒 SuperShop <span class="text-blue-400">Bangladesh</span>
    </a>
    <div class="flex gap-2 text-sm">
      <a href="/"          class="px-3 py-1.5 rounded hover:bg-gray-700 transition">Dashboard</a>
      <a href="/branches"  class="px-3 py-1.5 rounded hover:bg-gray-700 transition">Branches</a>
      <a href="/products"  class="px-3 py-1.5 rounded hover:bg-gray-700 transition">Products</a>
      <a href="/sales"     class="px-3 py-1.5 rounded hover:bg-gray-700 transition">Sales</a>
      <a href="/customers" class="px-3 py-1.5 rounded hover:bg-gray-700 transition">Customers</a>
      <a href="/inventory" class="px-3 py-1.5 rounded hover:bg-gray-700 transition">Inventory</a>
      <a href="/docs"      class="px-3 py-1.5 rounded bg-blue-600 hover:bg-blue-700 transition"
         target="_blank">API Docs ↗</a>
    </div>
  </nav>

  <!-- ── PAGE CONTENT ── -->
  <main class="max-w-7xl mx-auto px-6 py-8">
    {% block content %}{% endblock %}
  </main>

  <!-- ── FOOTER ── -->
  <footer class="text-center text-gray-400 text-xs py-6 mt-8 border-t border-gray-200">
    SuperShop Bangladesh · CSE-2201 Lab Project · University of Dhaka 2025
  </footer>

</body>
</html>
```

---

### templates/index.html  (Dashboard)

```html
{% extends "base.html" %}
{% block title %}Dashboard{% endblock %}

{% block content %}
<h1 class="text-2xl font-bold text-gray-800 mb-6">Dashboard</h1>

<!-- ── STAT CARDS ── -->
<div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">

  <div class="bg-white rounded-xl shadow p-5 border-l-4 border-blue-500">
    <p class="text-sm text-gray-500 mb-1">Active Branches</p>
    <p class="text-3xl font-bold text-blue-600">{{ stats.branches }}</p>
  </div>

  <div class="bg-white rounded-xl shadow p-5 border-l-4 border-green-500">
    <p class="text-sm text-gray-500 mb-1">Products</p>
    <p class="text-3xl font-bold text-green-600">{{ stats.products }}</p>
  </div>

  <div class="bg-white rounded-xl shadow p-5 border-l-4 border-purple-500">
    <p class="text-sm text-gray-500 mb-1">Customers</p>
    <p class="text-3xl font-bold text-purple-600">{{ stats.customers }}</p>
  </div>

  <div class="bg-white rounded-xl shadow p-5 border-l-4 border-orange-500">
    <p class="text-sm text-gray-500 mb-1">Employees</p>
    <p class="text-3xl font-bold text-orange-500">{{ stats.employees }}</p>
  </div>

</div>

<!-- ── RECENT SALES TABLE ── -->
<div class="bg-white rounded-xl shadow">
  <div class="px-6 py-4 border-b border-gray-100">
    <h2 class="text-lg font-semibold text-gray-700">Recent Sales</h2>
  </div>
  <div class="overflow-x-auto">
    <table class="w-full text-sm">
      <thead class="bg-gray-50 text-gray-500 uppercase text-xs">
        <tr>
          <th class="px-4 py-3 text-left">Sale ID</th>
          <th class="px-4 py-3 text-left">Date</th>
          <th class="px-4 py-3 text-left">Branch</th>
          <th class="px-4 py-3 text-left">Customer</th>
          <th class="px-4 py-3 text-right">Total (BDT)</th>
          <th class="px-4 py-3 text-center">Type</th>
          <th class="px-4 py-3 text-center">Status</th>
        </tr>
      </thead>
      <tbody class="divide-y divide-gray-100">
        {% for s in recent_sales %}
        <tr class="hover:bg-gray-50">
          <td class="px-4 py-3 font-mono text-blue-600">{{ s.sale_id }}</td>
          <td class="px-4 py-3 text-gray-500">{{ s.sale_date }}</td>
          <td class="px-4 py-3">{{ s.branch_name }}</td>
          <td class="px-4 py-3">{{ s.customer }}</td>
          <td class="px-4 py-3 text-right font-semibold">
            {{ "%.2f"|format(s.total_amt) }}
          </td>
          <td class="px-4 py-3 text-center">
            {% if s.order_type == 'ONLINE' %}
              <span class="bg-blue-100 text-blue-700 px-2 py-0.5 rounded-full text-xs">Online</span>
            {% else %}
              <span class="bg-gray-100 text-gray-600 px-2 py-0.5 rounded-full text-xs">In-Store</span>
            {% endif %}
          </td>
          <td class="px-4 py-3 text-center">
            {% if s.payment_status == 'PAID' %}
              <span class="bg-green-100 text-green-700 px-2 py-0.5 rounded-full text-xs">Paid</span>
            {% elif s.payment_status == 'PENDING' %}
              <span class="bg-yellow-100 text-yellow-700 px-2 py-0.5 rounded-full text-xs">Pending</span>
            {% else %}
              <span class="bg-red-100 text-red-700 px-2 py-0.5 rounded-full text-xs">Cancelled</span>
            {% endif %}
          </td>
        </tr>
        {% endfor %}
      </tbody>
    </table>
  </div>
</div>
{% endblock %}
```

---

### templates/products.html

```html
{% extends "base.html" %}
{% block title %}Products{% endblock %}

{% block content %}
<div class="flex items-center justify-between mb-6">
  <h1 class="text-2xl font-bold text-gray-800">Products</h1>
  <input id="searchBox" type="text" placeholder="Search products..."
    class="border border-gray-300 rounded-lg px-4 py-2 text-sm
           focus:outline-none focus:ring-2 focus:ring-blue-400 w-64">
</div>

<div class="bg-white rounded-xl shadow overflow-x-auto">
  <table class="w-full text-sm" id="productTable">
    <thead class="bg-gray-800 text-white text-xs uppercase">
      <tr>
        <th class="px-4 py-3 text-left">ID</th>
        <th class="px-4 py-3 text-left">Name</th>
        <th class="px-4 py-3 text-left">Brand</th>
        <th class="px-4 py-3 text-left">Category</th>
        <th class="px-4 py-3 text-left">Supplier</th>
        <th class="px-4 py-3 text-right">Price (BDT)</th>
        <th class="px-4 py-3 text-center">Unit</th>
        <th class="px-4 py-3 text-center">Status</th>
      </tr>
    </thead>
    <tbody class="divide-y divide-gray-100" id="productBody">
      {% for p in products %}
      <tr class="hover:bg-gray-50">
        <td class="px-4 py-3 font-mono text-blue-600 text-xs">{{ p.product_id }}</td>
        <td class="px-4 py-3 font-medium">{{ p.product_name }}</td>
        <td class="px-4 py-3 text-gray-500">{{ p.brand or '—' }}</td>
        <td class="px-4 py-3">
          <span class="bg-purple-100 text-purple-700 px-2 py-0.5 rounded text-xs">
            {{ p.cat_name or '—' }}
          </span>
        </td>
        <td class="px-4 py-3 text-gray-500 text-xs">{{ p.supplier_name or '—' }}</td>
        <td class="px-4 py-3 text-right font-semibold">{{ "%.2f"|format(p.unit_price) }}</td>
        <td class="px-4 py-3 text-center text-gray-500">{{ p.unit }}</td>
        <td class="px-4 py-3 text-center">
          {% if p.is_active == 'Y' %}
            <span class="bg-green-100 text-green-700 px-2 py-0.5 rounded-full text-xs">Active</span>
          {% else %}
            <span class="bg-red-100 text-red-700 px-2 py-0.5 rounded-full text-xs">Inactive</span>
          {% endif %}
        </td>
      </tr>
      {% endfor %}
    </tbody>
  </table>
</div>

<script>
  document.getElementById('searchBox').addEventListener('input', function () {
    const term = this.value.toLowerCase();
    document.querySelectorAll('#productBody tr').forEach(row => {
      row.style.display = row.innerText.toLowerCase().includes(term) ? '' : 'none';
    });
  });
</script>
{% endblock %}
```

---

### templates/customers.html

```html
{% extends "base.html" %}
{% block title %}Customers{% endblock %}

{% block content %}
<div class="flex items-center justify-between mb-6">
  <h1 class="text-2xl font-bold text-gray-800">Customers</h1>
  <input id="searchBox" type="text" placeholder="Search by name, phone..."
    class="border border-gray-300 rounded-lg px-4 py-2 text-sm
           focus:outline-none focus:ring-2 focus:ring-blue-400 w-64">
</div>

<div class="bg-white rounded-xl shadow overflow-x-auto">
  <table class="w-full text-sm">
    <thead class="bg-gray-800 text-white text-xs uppercase">
      <tr>
        <th class="px-4 py-3 text-left">ID</th>
        <th class="px-4 py-3 text-left">Name</th>
        <th class="px-4 py-3 text-left">Email</th>
        <th class="px-4 py-3 text-left">Phone</th>
        <th class="px-4 py-3 text-center">Gender</th>
        <th class="px-4 py-3 text-center">Membership</th>
        <th class="px-4 py-3 text-right">Points</th>
        <th class="px-4 py-3 text-left">Joined</th>
      </tr>
    </thead>
    <tbody class="divide-y divide-gray-100" id="custBody">
      {% for c in customers %}
      <tr class="hover:bg-gray-50">
        <td class="px-4 py-3 font-mono text-blue-600 text-xs">{{ c.cust_id }}</td>
        <td class="px-4 py-3 font-medium">{{ c.cust_name }}</td>
        <td class="px-4 py-3 text-gray-500 text-xs">{{ c.email }}</td>
        <td class="px-4 py-3 text-gray-500">{{ c.phone }}</td>
        <td class="px-4 py-3 text-center">
          {{ '👨' if c.gender == 'M' else '👩' }}
        </td>
        <td class="px-4 py-3 text-center">
          {% set tier_colors = {
            'PLATINUM': 'bg-indigo-100 text-indigo-800',
            'GOLD':     'bg-yellow-100 text-yellow-800',
            'SILVER':   'bg-gray-200 text-gray-700',
            'REGULAR':  'bg-green-100 text-green-700'
          } %}
          <span class="px-2 py-0.5 rounded-full text-xs font-medium
                       {{ tier_colors.get(c.membership_type, 'bg-gray-100') }}">
            {{ c.membership_type }}
          </span>
        </td>
        <td class="px-4 py-3 text-right font-semibold text-blue-700">
          {{ "{:,}".format(c.loyalty_points) }}
        </td>
        <td class="px-4 py-3 text-gray-400 text-xs">{{ c.join_date }}</td>
      </tr>
      {% endfor %}
    </tbody>
  </table>
</div>

<script>
  document.getElementById('searchBox').addEventListener('input', function () {
    const term = this.value.toLowerCase();
    document.querySelectorAll('#custBody tr').forEach(row => {
      row.style.display = row.innerText.toLowerCase().includes(term) ? '' : 'none';
    });
  });
</script>
{% endblock %}
```

---

### templates/sales.html

```html
{% extends "base.html" %}
{% block title %}Sales{% endblock %}

{% block content %}
<div class="flex items-center justify-between mb-6">
  <h1 class="text-2xl font-bold text-gray-800">Sales</h1>
  <div class="flex gap-2">
    <select id="statusFilter"
      class="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none">
      <option value="">All Status</option>
      <option value="PAID">Paid</option>
      <option value="PENDING">Pending</option>
      <option value="CANCELLED">Cancelled</option>
    </select>
    <select id="typeFilter"
      class="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none">
      <option value="">All Types</option>
      <option value="IN_STORE">In-Store</option>
      <option value="ONLINE">Online</option>
    </select>
  </div>
</div>

<div class="bg-white rounded-xl shadow overflow-x-auto">
  <table class="w-full text-sm">
    <thead class="bg-gray-800 text-white text-xs uppercase">
      <tr>
        <th class="px-4 py-3 text-left">Sale ID</th>
        <th class="px-4 py-3 text-left">Date</th>
        <th class="px-4 py-3 text-left">Branch</th>
        <th class="px-4 py-3 text-left">Customer</th>
        <th class="px-4 py-3 text-left">Employee</th>
        <th class="px-4 py-3 text-right">Subtotal</th>
        <th class="px-4 py-3 text-right">Discount</th>
        <th class="px-4 py-3 text-right">Total</th>
        <th class="px-4 py-3 text-center">Type</th>
        <th class="px-4 py-3 text-center">Status</th>
      </tr>
    </thead>
    <tbody class="divide-y divide-gray-100" id="salesBody">
      {% for s in sales %}
      <tr class="hover:bg-gray-50" data-status="{{ s.payment_status }}"
          data-type="{{ s.order_type }}">
        <td class="px-4 py-3 font-mono text-blue-600 text-xs">{{ s.sale_id }}</td>
        <td class="px-4 py-3 text-gray-500 text-xs">{{ s.sale_date }}</td>
        <td class="px-4 py-3">{{ s.branch_name }}</td>
        <td class="px-4 py-3">{{ s.customer }}</td>
        <td class="px-4 py-3 text-gray-500">{{ s.emp_name }}</td>
        <td class="px-4 py-3 text-right">{{ "%.2f"|format(s.subtotal) }}</td>
        <td class="px-4 py-3 text-right text-red-500">
          {% if s.discount_amt > 0 %}-{{ "%.2f"|format(s.discount_amt) }}{% else %}—{% endif %}
        </td>
        <td class="px-4 py-3 text-right font-bold">{{ "%.2f"|format(s.total_amt) }}</td>
        <td class="px-4 py-3 text-center">
          {% if s.order_type == 'ONLINE' %}
            <span class="bg-blue-100 text-blue-700 px-2 py-0.5 rounded-full text-xs">Online</span>
          {% else %}
            <span class="bg-gray-100 text-gray-600 px-2 py-0.5 rounded-full text-xs">In-Store</span>
          {% endif %}
        </td>
        <td class="px-4 py-3 text-center">
          {% if s.payment_status == 'PAID' %}
            <span class="bg-green-100 text-green-700 px-2 py-0.5 rounded-full text-xs">Paid</span>
          {% elif s.payment_status == 'PENDING' %}
            <span class="bg-yellow-100 text-yellow-700 px-2 py-0.5 rounded-full text-xs">Pending</span>
          {% else %}
            <span class="bg-red-100 text-red-700 px-2 py-0.5 rounded-full text-xs">Cancelled</span>
          {% endif %}
        </td>
      </tr>
      {% endfor %}
    </tbody>
  </table>
</div>

<script>
  function applyFilters() {
    const status = document.getElementById('statusFilter').value;
    const type   = document.getElementById('typeFilter').value;
    document.querySelectorAll('#salesBody tr').forEach(row => {
      const matchStatus = !status || row.dataset.status === status;
      const matchType   = !type   || row.dataset.type   === type;
      row.style.display = (matchStatus && matchType) ? '' : 'none';
    });
  }
  document.getElementById('statusFilter').addEventListener('change', applyFilters);
  document.getElementById('typeFilter').addEventListener('change', applyFilters);
</script>
{% endblock %}
```

---

### templates/branches.html

```html
{% extends "base.html" %}
{% block title %}Branches{% endblock %}

{% block content %}
<h1 class="text-2xl font-bold text-gray-800 mb-6">Branches</h1>

<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
  {% for b in branches %}
  <div class="bg-white rounded-xl shadow p-5 border-t-4
              {{ 'border-green-500' if b.is_active == 'Y' else 'border-gray-300' }}">

    <div class="flex justify-between items-start mb-2">
      <h2 class="font-bold text-gray-800 text-base">{{ b.branch_name }}</h2>
      {% if b.is_active == 'Y' %}
        <span class="bg-green-100 text-green-700 text-xs px-2 py-0.5 rounded-full">Active</span>
      {% else %}
        <span class="bg-gray-100 text-gray-500 text-xs px-2 py-0.5 rounded-full">Inactive</span>
      {% endif %}
    </div>

    <p class="text-xs font-mono text-blue-500 mb-3">{{ b.branch_id }}</p>

    <div class="text-sm text-gray-600 space-y-1">
      <p>📍 {{ b.city_name }}</p>
      <p>🏠 {{ b.address }}</p>
      <p>📞 {{ b.phone or '—' }}</p>
      <p>🕐 {{ b.open_time }} – {{ b.close_time }}</p>
      <p>👔 <span class="font-medium">{{ b.manager_name or 'No manager assigned' }}</span></p>
    </div>
  </div>
  {% endfor %}
</div>
{% endblock %}
```

---

## 4. RUNNING LOCALLY (VS Code terminal)

Open VS Code terminal (Ctrl + ` backtick), then run these commands
one by one — only do the venv steps once:

```bash
# Step 1: create virtual environment (only once)
python -m venv venv

# Step 2: activate it
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# Step 3: install packages (only once, or after requirements.txt changes)
pip install -r requirements.txt

# Step 4: start the server
uvicorn main:app --reload
```

Then open browser:
- http://localhost:8000          → Dashboard
- http://localhost:8000/products → Products page
- http://localhost:8000/docs     → Auto API documentation  ← show this in presentation!

The `--reload` flag means the server restarts automatically every time
you save a file. You don't need to stop and restart manually.

---

## 5. DEPLOY ON RAILWAY (step by step)

### 5a. Push to GitHub

```bash
# In VS Code terminal:
git init
git add .
git commit -m "first commit"
```

Go to github.com → New repository → name it `supershop-web`
→ copy the commands GitHub shows you (they look like):

```bash
git remote add origin https://github.com/YOUR_USERNAME/supershop-web.git
git branch -M main
git push -u origin main
```

### 5b. Deploy on Railway

1. Go to https://railway.app → Sign up with GitHub
2. Click "New Project" → "Deploy from GitHub repo"
3. Select your `supershop-web` repository
4. Railway detects Python automatically and starts building

### 5c. Add PostgreSQL on Railway

1. Inside your Railway project, click "+ New"
2. Select "Database" → "Add PostgreSQL"
3. Railway creates a PostgreSQL instance for you

### 5d. Import your database

1. Click the PostgreSQL service → "Data" tab → "Connect"
2. Copy the connection string (looks like postgresql://...)
3. Use pgAdmin or psql to run your DDL and INSERT scripts on this URL:

```bash
psql "postgresql://postgres:xxxx@xxx.railway.app:5432/railway" -f schema.sql
psql "postgresql://postgres:xxxx@xxx.railway.app:5432/railway" -f data.sql
```

### 5e. Link DATABASE_URL

1. Click your Flask/FastAPI service in Railway
2. Go to "Variables" tab
3. Railway should already show DATABASE_URL from the linked PostgreSQL
4. If not: click "Add Variable" → DATABASE_URL → paste the connection string

### 5f. Get your live URL

Railway gives you a free domain like:
`https://supershop-web-production.up.railway.app`

Every time you `git push`, Railway redeploys automatically.

---

## 6. CHEATSHEET — Most Common Mistakes

| Problem | Fix |
|---|---|
| `ModuleNotFoundError: fastapi` | Did you activate venv? Run `venv\Scripts\activate` first |
| `address already in use` | Port 8000 is busy. Run `uvicorn main:app --reload --port 8001` |
| Templates not found | Make sure folder is named `templates` (lowercase), not `Templates` |
| `.env` not working | Make sure `load_dotenv()` is called at the top of `database.py` |
| Railway deploy fails | Check that `Procfile` has no typos and `requirements.txt` is complete |
| Blank page on Railway | DATABASE_URL variable missing — check Railway Variables tab |

---

## 7. WHAT TO SHOW IN PRESENTATION

1. Open the live Railway URL — show the Dashboard with stat cards
2. Go to /products — demo the live search box
3. Go to /sales — demo the filter dropdowns
4. Go to /branches — show the card layout
5. **Go to /docs** — this is the most impressive part.
   FastAPI auto-generates an interactive API page. Click any endpoint,
   click "Try it out", click "Execute" — it runs the SQL live.
   This proves your database queries work.

---
```