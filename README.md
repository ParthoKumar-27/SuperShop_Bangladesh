# 🛒 Supershop Bangladesh Management System

A multi-city retail platform for a supershop chain in Bangladesh, built end-to-end as a CSE‑2201 Database Management Systems project at the University of Dhaka. It ships a **21-table relational schema**, a **FastAPI + Jinja2 web application** with six role-based portals, and an integrated workflow that covers **browsing the storefront**, **shopping online**, **checking out in-store at the POS**, and **last-mile delivery** — all backed by the same PostgreSQL database.

> Three first-class experiences share one database: a **public storefront** that anonymous visitors can browse, a **customer portal** with a branch-locked cart, checkout, and order tracking, and a **branch-scoped employee back-office** with separate dashboards for cashiers, branch managers, sales staff, riders, and HQ admins.

## 📑 Contents

1. [Highlights](#-highlights)
2. [Project Structure](#-project-structure)
3. [Database Design](#-database-design)
4. [Web Application](#-web-application) — storefront · customer · employee · admin · auth
5. [Tech Stack](#-tech-stack)
6. [Environment Variables](#-environment-variables-env)
7. [Local Setup](#-local-setup-windows--macos--linux)
8. [Demo Credentials](#-demo-credentials-from-seed-data)
9. [Deployment (Vercel)](#-deployment-vercel)
10. [Feature Map → Code Locations](#-feature-map--code-locations)
11. [Troubleshooting](#-troubleshooting)
12. [Course Context](#-course-context)
13. [License](#-license)

---

## ✨ Highlights

- **21-table relational schema** (city → branch → employee → product → sale → online_order → payment → delivery) with full referential integrity, CHECK constraints, triggers, and analytic views.
- **Six role-based portals**, each with its own dashboard and permission model:
  - **Admin (HQ)** — products, branches, discounts, employees, suppliers, sales, inventory, audit logs.
  - **Branch Manager** — branch-scoped dashboard, staff, inventory, orders, sales.
  - **Cashier** — POS with phone lookup, cart-style bill builder, receipt printing.
  - **Sales Staff** — branch product catalog management.
  - **Delivery Rider** — assigned deliveries, status updates.
  - **Customer** — storefront, cart locked to a chosen branch, checkout, invoices, order tracking.
- **Public storefront** at `/` — categories, search, hot-deals carousel, branch-aware product cards, single-click add-to-cart, quick-view modal, wishlist.
- **Branch-locked cart** — every cart entry records the `branch_id` it came from, so the storefront, shop, and checkout all stay coherent even if the customer switches devices.
- **Discount engine** — percent and flat-amount discounts, scoped per-product or per-category, with start/end dates; automatically applied at storefront, POS, and invoice time.
- **Notifications & audit log** — bell-dropdown notifications per role, plus an HQ-only action log of sensitive operations.
- **Supabase storage integration** for product images (upload, render, cleanup on delete).
- **Multi-DBMS support** — DDL is written so it runs on both **PostgreSQL 16** and **Oracle 21c XE** (CHECK patterns use what both engines accept; sequence/trigger syntax in the deploy notes).
- **One-click Vercel deploy** via `vercel.json` (FastAPI on `@vercel/python`).

---

## 🧱 Project Structure

```
DBMS_Project-1/
├── main.py                 # Composition root — wires routers, error handlers, storefront
├── app_setup.py            # FastAPI() bootstrap, session middleware, NoCacheHTMLMiddleware, template/static mounts
├── auth.py                 # /auth/login, register, logout, phone lookup (3 roles + admin)
├── customer.py             # Customer portal: storefront API, shop, cart, checkout, invoice, profile
├── employee.py             # Employee portal: branch manager / cashier / sales staff / rider
├── admin.py                # Admin portal: HQ dashboards for every domain
├── branch_routes.py        # Branch + city + branch-manager management APIs
├── storefront_routes.py    # Public storefront, search, hot-deals, image URL normalization
├── notifications.py        # Shared notification + bell-dropdown helpers
├── action_logger.py        # Admin-only action_log writer
├── error_handlers.py       # 403 / 404 pages, FastAPI shutdown hook
├── database.py             # psycopg2 connection helper, query() wrapper
├── supabase_client.py      # Supabase storage client (product image upload/delete)
├── generate_hash.py        # Utility to seed bcrypt hashes
│
├── database_schema/
│   ├── Supershop.sql              # All 21 tables, sequences, triggers, views (incl. app_user + admin_account)
│   ├── Supershop_Data.sql         # Seed data for cities, branches, products, employees, sales, etc.
│   └── Fixed_Supershop_Query.sql  # Lab queries (Q1–Q10+) — JOINs, aggregations, triggers
│
├── templates/                     # Jinja2 — server-rendered HTML
│   ├── storefront.html            #   Public landing page
│   ├── authentication/login.html  #   Single login page — chooses Admin / Employee / Customer
│   ├── admin/                     #   HQ admin portal (12 pages)
│   ├── customer/                  #   Customer portal (10 pages)
│   ├── employee/                  #   Employee portal, role-split:
│   │   ├── branch_manager/        #     Branch manager dashboards
│   │   ├── cashier/               #     Cashier POS + receipt
│   │   ├── sales_staff/           #     Sales-staff product tools
│   │   └── rider/                 #     Rider delivery console
│   └── errors/                    #   404 page
│
├── static/                        # Static assets served by FastAPI
├── requirements.txt               # Python deps (fastapi, psycopg2-binary, supabase, …)
├── vercel.json                    # Vercel: @vercel/python → main.py
├── Procfile                       # Heroku/Railway entrypoint (unused on Vercel; kept for portability)
└── README.md                      # You are here
```

---

## 🗄️ Database Design

### Tables (21 total)

| Group | Tables |
|---|---|
| Geography | `city`, `branch` |
| People | `customer`, `membership`, `department`, `employee`, `branch_manager` (trigger-enforced: only `position = 'BRANCH_MANAGER'` may manage a branch) |
| Catalog | `category` (self-referential for sub-categories), `supplier`, `product` |
| Inventory & Promotions | `branch_inventory`, `discount` (per-product or per-category) |
| Sales | `sale`, `sale_item` |
| Online Orders | `online_order`, `payment`, `delivery` |
| Auth | `app_user` (employee + customer logins), `admin_account` |
| Platform | `notification`, `action_log` |

### Integrity & automation

- **CHECK constraints** on IDs (`branch_id LIKE 'B-____'`, `customer_id LIKE 'C-____'`, `emp_id LIKE 'E-____'`, `product_id LIKE 'P-____'`, `user_id LIKE 'U-%'`, etc.) so bad data can't be inserted.
- **Triggers** for branch-manager enforcement and audit-log writes.
- **Views / JOIN-ready** — every screen is a single query, no N+1, no ORM.

### Lab queries

`database_schema/Fixed_Supershop_Query.sql` contains the analytical and operational queries used in the course report — JOIN with ON, JOIN with USING, multi-table aggregations, branch-wise sales summaries, top-selling products, inventory gaps, trigger demos, etc.

---

## 🌐 Web Application

### Public storefront (`/`, `/search`)

- Hero carousel, features strip, top categories grid.
- **Hot-deals carousel** populated from `discount ⋈ product` where `CURRENT_DATE BETWEEN start_date AND end_date`.
- Branch-aware product grid — each card shows whether it's stocked in the currently selected branch and blocks adds for SKUs that aren't there.
- **Inline add-to-cart** (orange plus icon) — populates the session cart in place, no full-page reload. Branch-picker modal pops on the very first add per cart.
- **Quick-view modal** for fast product previews.
- **Wishlist** persisted in `localStorage`.
- Anonymous-friendly: anyone can browse; only adding to cart triggers the customer login redirect.

### Customer portal

- `dashboard`, `shop` (paginated grid), `category/:id`, `branches`, `cart`, `checkout`, `invoice/:sale_id` (HTML + JSON), `profile` (edit + password change + delete account), `inventory`.
- Cart is **branch-locked**: each entry is `{product_id: {qty, branch_id}}`. Adding a product from a *different* branch is refused with a toast, and the cart count badge updates live via `fetch()`.
- Notifications bell-dropdown with mark-as-read endpoints.
- Self-service order cancellation while a sale is still in `pending`.

### Employee portal (role-split)

- **Branch Manager** — `/employee/branch/dashboard` (alt: `/employee/dashboard/branch_manager`), `/employee/branch/sales`, `/employee/branch/products`, `/employee/branch/orders` (status transitions + rider assignment), `/employee/branch/staff`, `/employee/branch/inventory` (add/edit/delete).
- **Cashier** — `/employee/cashier/dashboard`, `/employee/cashier/lookup` (phone-based customer find), `/employee/cashier/inventory` (branch stock), `POST /employee/cashier/sale/submit` (POS bill builder), `/employee/cashier/bill/{sale_id}` (receipt JSON), `/employee/cashier/sales`. `/employee/branch/order-bill/{order_id}` lets a cashier/branch manager print a customer's online-order receipt.
- **Sales Staff** — `/employee/sales_staff/dashboard` plus product-catalog tooling scoped to their branch.
- **Rider** — `/employee/delivery_rider/dashboard` (assigned deliveries + today's stats), `POST /employee/rider/update-status` (mark delivery progress; auto-promotes order status and auto-marks COD payments PAID on `DELIVERED`).
- All branch-scoped queries include a `WHERE branch_id = :session_branch` filter so an employee at one branch can never see another branch's data.

### Admin portal

- `dashboard` (HQ-wide KPIs), `customers`, `employees` (activate/deactivate/edit), `branches` (city + branch CRUD), `manage_branches` (assign/reassign branch managers, create the manager employee inline), `products` (add/edit + image upload via Supabase), `discounts` (add/modify/delete, percent or flat), `sales`, `inventory`, `suppliers`, `logs` (action_log viewer), `profile`.
- Mutations are funnelled through `action_logger.py` so sensitive operations land in the audit log.

### Auth

- One `/auth/login` page handles **Admin** (username + password against `admin_account`), **Employee** (phone + password against `app_user` with `role = 'EMPLOYEE'`), and **Customer** (phone + password against `app_user` with `role = 'CUSTOMER'`).
- `/auth/customer/lookup` and `/auth/customer/register` enable phone-based self-service customer onboarding.
- Bcrypt-hashed passwords. Session middleware (server-side signed cookie, 32-char `SECRET_KEY`).

---

## 🧰 Tech Stack

| Layer | Choice |
|---|---|
| Backend | **FastAPI** (async-friendly; here used with sync `psycopg2` via a `query()` helper) |
| Templating | **Jinja2** server-side rendering — no SPA, no JS framework |
| Database | **PostgreSQL 16** for production; DDL is portable to **Oracle 21c XE** |
| Object storage | **Supabase Storage** (`Images` bucket) for product images |
| Auth | **bcrypt** + signed session cookies (`itsdangerous`) |
| Deploy target | **Vercel** (`vercel.json`, `@vercel/python`) |

`requirements.txt`:

```
fastapi
uvicorn
jinja2
aiofiles
psycopg2-binary
python-dotenv
python-multipart
bcrypt
itsdangerous
supabase
```

---

## ⚙️ Environment Variables (`.env`)

```env
DATABASE_URL=postgresql://postgres:yourpassword@localhost:5432/SuperShop
SECRET_KEY=any-random-32-character-string-here

SUPABASE_URL=https://<project-ref>.supabase.co
SUPABASE_SERVICE_ROLE_KEY=<service-role-key>
```

`SUPABASE_URL` / `SUPABASE_SERVICE_ROLE_KEY` are only required if you use the **product image upload** flow in the admin portal. Everything else works on plain PostgreSQL alone.

---

## 🚀 Local Setup (Windows / macOS / Linux)

### 1. One-time tool installs

- **Python 3.11+** — https://python.org/downloads
- **VS Code** — https://code.visualstudio.com  *(recommended extensions below)*
- **PostgreSQL 16** — https://www.postgresql.org/download/
- **Git** — https://git-scm.com

### 2. Recommended VS Code extensions

`Python` · `Pylance` · `Thunder Client` (test API endpoints without Postman) · `HTML CSS Support` · `Auto Rename Tag` · `Prettier` · `GitLens`.

### 3. Create and activate a virtual env

```bash
# from the project root
python -m venv venv
# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

### 5. Provision the database

Create an empty database (e.g. `SuperShop`) in PostgreSQL, then run the DDL + seed in this order:

```bash
psql -d SuperShop -f database_schema/Supershop.sql
psql -d SuperShop -f database_schema/Supershop_Data.sql
```

> All 21 tables (including the two auth tables `app_user` and `admin_account`) live in a single DDL file — `database_schema/Supershop.sql`. There is no separate `auth.sql`.

The lab/demo queries are in `database_schema/Fixed_Supershop_Query.sql` — open in psql or pgAdmin when you want to demo them.

### 6. Configure `.env`

```env
DATABASE_URL=postgresql://postgres:yourpassword@localhost:5432/SuperShop
SECRET_KEY=any-random-32-character-string-here
```

### 7. Run

```bash
uvicorn main:app --reload
```

Then open:

| URL | Purpose |
|---|---|
| `http://localhost:8000/` | Public storefront |
| `http://localhost:8000/search?q=…` | Search the catalog |
| `http://localhost:8000/auth/login` | Sign-in (Admin / Employee / Customer) |
| `http://localhost:8000/docs` | **FastAPI auto-generated interactive API docs** |

`--reload` restarts the server on every save, so you don't need to restart manually.

---

## 🔑 Demo Credentials (from seed data)

After running `Supershop_Data.sql`, you can sign in with these sample accounts. **Change all of these in production.**

| Role | Login field | Sample value | Password |
|---|---|---|---|
| **Admin (HQ)** | `admin_id` | `ADM-001` | `admin123` |
| **Branch Manager** | phone | `01711-100001` | `employee123` |
| **Cashier** | phone | `01911-100007` | `employee123` |
| **Sales Staff** | phone | `01911-100011` | `employee123` |
| **Delivery Rider** | phone | `01812-200001` | `employee123` |
| **Customer** | phone | `01711-000001` | `customer123` |

> All employee passwords share the same bcrypt hash (`employee123`); customer passwords share `customer123`. To generate a fresh hash, run `python generate_hash.py`.

---

## ☁️ Deployment (Vercel)

This project is deployed on **Vercel** using `@vercel/python`. `vercel.json` is already configured for FastAPI:

```json
{
  "version": 2,
  "builds": [{ "src": "main.py", "use": "@vercel/python" }],
  "routes": [{ "src": "/(.*)", "dest": "main.py" }]
}
```

### 1. Push to GitHub

```bash
git init
git add .
git commit -m "first commit"
git branch -M main
git remote add origin https://github.com/<your-username>/DBMS_Project.git
git push -u origin main
```

### 2. Import the project on Vercel

1. Go to https://vercel.com → **Add New → Project** → import the GitHub repo.
2. Vercel auto-detects `vercel.json` and uses `@vercel/python`. No build command override needed.

### 3. Provision the database

Vercel serverless functions are stateless, so you need an **externally-hosted PostgreSQL** (Neon, Supabase Postgres, Railway Postgres, etc.):

1. Create a PostgreSQL database and copy its connection string.
2. Run the schema in order against that database:
   ```bash
   psql "<connection-string>" -f database_schema/Supershop.sql
   psql "<connection-string>" -f database_schema/Supershop_Data.sql
   ```
   (All 21 tables, including `app_user` + `admin_account`, are in `Supershop.sql` — there is no separate `auth.sql`.)

### 4. Set environment variables

In Vercel → Project → **Settings → Environment Variables**, add:

| Variable | Value |
|---|---|
| `DATABASE_URL` | The PostgreSQL connection string from step 3 |
| `SECRET_KEY` | Any random 32-character string (used to sign session cookies) |
| `SUPABASE_URL` | *(optional)* `https://<project-ref>.supabase.co` — needed for product image upload |
| `SUPABASE_SERVICE_ROLE_KEY` | *(optional)* service-role key from Supabase — needed for product image upload |

### 5. Deploy

Every `git push` to `main` triggers a redeploy. Vercel gives you a free URL like `https://dbms-project.vercel.app`.

> **Note on Vercel + sessions:** Vercel serverless functions are stateless, so the signed session cookie is the only thing that persists between requests. Make sure `SECRET_KEY` stays the same across deploys — rotating it invalidates every active customer/employee/admin session.

---

## 🧪 Feature Map → Code Locations

| Feature | Where to look |
|---|---|
| Public storefront (`/`) | `storefront_routes.py` + `templates/storefront.html` |
| Search (`/search`) | `storefront_routes.py::public_search` |
| Customer auth | `auth.py` (admin / employee / customer login + customer register + lookup) |
| Customer shop / cart / checkout / invoice | `customer.py` + `templates/customer/*` |
| Branch-locked cart logic | `customer.py::_cart_locked_branch`, `_cart_iter` |
| Cashier POS | `employee.py::/employee/cashier/sale/submit` + `templates/employee/cashier/pos.html` |
| Rider delivery updates | `employee.py::/employee/rider/update-status` + `templates/employee/rider/deliveries.html` |
| Branch manager orders + rider assignment | `employee.py::/employee/branch/orders/*` + `templates/employee/branch_manager/orders.html` |
| Admin product image upload | `admin.py::/admin/dashboard/products/add` + `supabase_client.py::upload_product_image` |
| Discount CRUD | `admin.py::/admin/dashboard/discounts/*` + `templates/admin/discounts.html` |
| Audit log | `admin.py::/admin/dashboard/logs` + `action_logger.py` |
| Branch / city / branch-manager CRUD | `branch_routes.py` (mounted at `/admin/branches/*`) |
| Notifications | `notifications.py` + bell-dropdown endpoints under `/notifications` per role |
| 21-table DDL | `database_schema/Supershop.sql` (includes `app_user` + `admin_account`) |
| Lab queries | `database_schema/Fixed_Supershop_Query.sql` |

---

## 🛠️ Troubleshooting

| Problem | Fix |
|---|---|
| `ModuleNotFoundError: fastapi` | Activate the venv first: `venv\Scripts\activate` (Win) / `source venv/bin/activate` (macOS/Linux). |
| `address already in use` | Port 8000 is busy: `uvicorn main:app --reload --port 8001`. |
| Templates not found | Folder must be `templates/` (lowercase), not `Templates/`. |
| `.env` values ignored | Make sure `python-dotenv::load_dotenv()` is called at the top of `database.py` / `supabase_client.py` before any `os.environ` lookup. |
| `psycopg2` install fails | Install PostgreSQL dev headers first, or switch to `psycopg2-binary` (already in `requirements.txt`). |
| Login doesn't redirect | Verify the `SECRET_KEY` is set and unchanged between requests — sessions won't survive a key rotation. |
| Vercel deploy fails | Check the *Deploy Logs* tab in Vercel; the most common cause is a missing/typo'd `DATABASE_URL` or `SECRET_KEY` env var. |
| Blank page on Vercel | `DATABASE_URL` variable missing — check Project → Settings → Environment Variables. |
| Product images not showing | Confirm `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY` are set in Vercel env vars, and the `Images` bucket is public-readable. |

---

## 📚 Course Context

> **Course:** CSE‑2201 — Database Management Systems
> **Semester:** 2nd Year, 2nd Semester 2025
> **University of Dhaka — Department of CSE**
> **DBMS:** PostgreSQL 16 (development) / Oracle 21c XE (coursework-compatible)

The project deliberately implements the full layered story required by the syllabus:

1. **Requirement analysis** → ER modeling (city / branch / product / sale / order / delivery).
2. **Relational mapping** → 21 tables (city, branch, membership, customer, department, employee, branch_manager, category, supplier, product, branch_inventory, discount, sale, sale_item, online_order, payment, delivery, app_user, admin_account, notification, action_log), all with PKs, FKs, `CHECK` constraints.
3. **Normalization** → every table is in 3NF; derived values (sale totals, inventory roll-ups) are computed at query time, not stored.
4. **Querying** → lab queries in `Fixed_Supershop_Query.sql` exercise JOIN styles, aggregations, sub-queries, triggers, and views.
5. **Application layer** → a working web system proves the schema is queryable end-to-end and usable by real (role-divided) users.

---

## 📄 License

Released under the **MIT License** — see [`LICENSE`](./LICENSE) for the full text.

You're free to use, copy, modify, and distribute this project.
