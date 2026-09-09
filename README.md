# 🛒 Supershop Bangladesh

> A multi-city retail management system — built end-to-end as a CSE‑2201 Database Management Systems project.

Supershop Bangladesh is a full-stack retail platform that runs a single PostgreSQL database behind **three user-facing experiences**: a public storefront, a customer portal, and a branch-scoped employee back-office. From browsing the catalog to checking out at the POS to delivering the order — every flow touches the same schema.

---

## ⚡ At a Glance

| | |
|---|---|
| **Schema** | 21 tables · CHECK constraints · triggers · analytic views |
| **Stack** | FastAPI · Jinja2 · PostgreSQL 16 · Supabase Storage |
| **Portals** | Storefront · Customer · Employee (5 roles) · Admin (HQ) |
| **DBMS** | PostgreSQL 16 (deploy) · Oracle 21c XE compatible (coursework) |
| **Deploy** | One-click on Vercel via `@vercel/python` |

---

## 🎯 What It Does

The platform serves **two distinct shopping paths** plus the staff that keeps them running.

### 🛍 Path 1 — Online (home delivery)

```
 Storefront  ──▶  Customer  ──▶  Online Order + Payment  ──▶  Branch Manager
   (browse)        (cart)          (checkout)                  (assigns rider)
                                                                     │
                                                                     ▼
                                                              ┌──────────────┐
                                                              │ Delivery     │
                                                              │ Rider        │
                                                              │ (delivers)   │
                                                              └──────────────┘
```

- Customer browses the public storefront, builds a **branch-locked cart**, checks out, and pays online (or COD).
- Branch manager reviews the order and **assigns a delivery rider**.
- Rider picks up, updates status; on `DELIVERED`, COD payments are auto-marked `PAID`.

### 🏬 Path 2 — In-store (walk-in purchase)

```
 Customer  ──▶  Cashier  ──▶  Bill + Payment  ──▶  Customer walks out with product
  (walks in)    (POS)
```

- Customer walks into a branch and picks items off the shelf.
- Cashier uses **phone lookup** to find or register the customer, builds a cart-style bill, and prints the receipt.
- No delivery, no online order — the customer leaves with the product the moment payment clears.


---

## 🧭 Contents

1. [Architecture](#-architecture)
2. [Database Design](#-database-design)
3. [Tech Stack](#-tech-stack)
4. [Quick Start](#-quick-start)
5. [Environment Variables](#-environment-variables)
6. [Demo Credentials](#-demo-credentials)
7. [Deployment](#-deployment)
8. [Project Structure](#-project-structure)
9. [Feature Map](#-feature-map)
10. [Troubleshooting](#-troubleshooting)
11. [Course Context](#-course-context)
12. [License](#-license)

---

## 📎 Project Documents

- 📄 [**Project Report**](./SuperShop_Bangladesh_Project_Report.pdf?raw=true) — full requirement analysis, ER/relational design, normalization, and lab queries.
- 🎞️ [**Presentation Slides**](./SuperShop_Bangladesh_Project_Presentation.pdf?raw=true) — system walkthrough, schema overview, and demo flow.

---

## 🏛 Architecture

```
Browser ──▶ FastAPI (Jinja2 SSR) ──▶ PostgreSQL 16
                │                         ▲
                │                         │
                ▼                         │
           Supabase Storage (product images)
```

- **Backend:** FastAPI with sync `psycopg2` via a single `query()` helper — no ORM, no N+1.
- **Templates:** Server-side rendered Jinja2; no SPA framework.
- **Auth:** bcrypt + signed session cookies (`itsdangerous`) — one login page handles Admin / Employee / Customer.
- **Audit:** Every sensitive mutation is funneled through `action_logger.py` into `action_log`.

### Role model

| Role | Surface | Scope |
|---|---|---|
| **Admin (HQ)** | `/admin/*` | Products, branches, discounts, employees, suppliers, sales, inventory, logs |
| **Branch Manager** | `/employee/branch/*` | Staff, inventory, orders, sales — branch-scoped |
| **Cashier** | `/employee/cashier/*` | POS, phone lookup, receipt printing |
| **Sales Staff** | `/employee/sales_staff/*` | Branch product catalog |
| **Delivery Rider** | `/employee/delivery_rider/*` | Assigned deliveries, status updates |
| **Customer** | `/customer/*` + `/` | Storefront, cart (branch-locked), checkout, invoices, tracking |

---

## 🗄 Database Design

### The 21 tables

| Group | Tables |
|---|---|
| **Geography** | `city`, `branch` |
| **People** | `customer`, `membership`, `department`, `employee`, `branch_manager` |
| **Catalog** | `category` *(self-referential)*, `supplier`, `product` |
| **Inventory & Promotions** | `branch_inventory`, `discount` *(per-product or per-category)* |
| **Sales** | `sale`, `sale_item` |
| **Online Orders** | `online_order`, `payment`, `delivery` |
| **Auth** | `app_user`, `admin_account` |
| **Platform** | `notification`, `action_log` |

### Why it holds together

- **CHECK constraints** on every ID (`B-____`, `C-____`, `E-____`, `P-____`, `U-%`, …) — bad rows never enter.
- **Triggers** enforce "only `BRANCH_MANAGER` may manage a branch" and write to the audit log.
- **3NF throughout** — derived totals (sale amount, inventory roll-ups) are computed at query time, never stored.
- **Lab queries** in `database_schema/Fixed_Supershop_Query.sql` exercise JOIN (ON/USING), aggregations, sub-queries, triggers, and views — one query per screen.

---

## 🧰 Tech Stack

| Layer | Choice |
|---|---|
| Backend | FastAPI |
| Templating | Jinja2 (SSR) |
| Database | PostgreSQL 16 · portable to Oracle 21c XE |
| Storage | Supabase Storage (`Images` bucket) |
| Auth | bcrypt · `itsdangerous` session cookies |
| Deploy | Vercel · `@vercel/python` |

---

## 🚀 Quick Start

**Prereqs:** Python 3.11+ · PostgreSQL 16 · Git

```bash
# 1. Clone & enter
git clone https://github.com/<your-username>/DBMS_Project.git
cd DBMS_Project

# 2. Virtual env
python -m venv venv
# Windows:      venv\Scripts\activate
# macOS/Linux:  source venv/bin/activate

# 3. Install deps
pip install -r requirements.txt

# 4. Create the database, then load schema + seed
createdb SuperShop
psql -d SuperShop -f database_schema/Supershop.sql
psql -d SuperShop -f database_schema/Supershop_Data.sql

# 5. Configure .env (see below), then run
uvicorn main:app --reload
```

Open **http://localhost:8000** for the storefront, or **http://localhost:8000/docs** for the auto-generated API explorer.

---

## 🔐 Environment Variables

Create a `.env` at the project root:

```env
# Required
DATABASE_URL=postgresql://postgres:yourpassword@localhost:5432/SuperShop
SECRET_KEY=any-random-32-character-string-here

# Optional — only needed for product image upload in the admin portal
SUPABASE_URL=https://<project-ref>.supabase.co
SUPABASE_SERVICE_ROLE_KEY=<service-role-key>
```

> `SECRET_KEY` signs your session cookies. Rotating it logs everyone out — keep it stable across deploys.

---

## 🔑 Demo Credentials

Loaded by `Supershop_Data.sql`. **Change before going to production.**

| Role | Field | Value | Password |
|---|---|---|---|
| Admin (HQ) | `admin_id` | `ADM-001` | `admin123` |
| Branch Manager | phone | `01711-100001` | `employee123` |
| Cashier | phone | `01911-100007` | `employee123` |
| Sales Staff | phone | `01911-100011` | `employee123` |
| Delivery Rider | phone | `01812-200001` | `employee123` |
| Customer | phone | `01711-000001` | `customer123` |

Generate a fresh bcrypt hash with `python generate_hash.py`.

---

## ☁ Deployment

Already configured for Vercel via `vercel.json`:

```json
{
  "version": 2,
  "builds": [{ "src": "main.py", "use": "@vercel/python" }],
  "routes": [{ "src": "/(.*)", "dest": "main.py" }]
}
```

1. **Push to GitHub**, then import on [vercel.com](https://vercel.com).
2. **Provision an external Postgres** (Neon, Supabase, Railway) — Vercel functions are stateless.
3. **Run the schema** against it:
   ```bash
   psql "$DATABASE_URL" -f database_schema/Supershop.sql
   psql "$DATABASE_URL" -f database_schema/Supershop_Data.sql
   ```
4. **Set env vars** in Vercel → Project → Settings → Environment Variables (`DATABASE_URL`, `SECRET_KEY`, plus `SUPABASE_*` if you want image upload).
5. **Deploy** — every `git push` to `main` redeploys.

---

## 📂 Project Structure

```
DBMS_Project-1/
├── main.py                      # Composition root — wires routers, middleware, storefront
├── app_setup.py                 # FastAPI() bootstrap, session middleware, template/static mounts
├── auth.py                      # Login · register · phone lookup (Admin / Employee / Customer)
├── customer.py                  # Customer portal: shop, cart, checkout, invoice, profile
├── employee.py                  # Employee portal: branch manager / cashier / sales / rider
├── admin.py                     # Admin portal: HQ dashboards across every domain
├── branch_routes.py             # Branch · city · branch-manager CRUD
├── storefront_routes.py         # Public storefront, search, hot-deals, image URLs
├── notifications.py             # Bell-dropdown helpers, shared across roles
├── action_logger.py             # Audit-log writer (admin-only mutations)
├── error_handlers.py            # 403 / 404 pages, FastAPI shutdown hook
├── database.py                  # psycopg2 connection helper + query() wrapper
├── supabase_client.py           # Supabase storage (image upload/delete)
├── generate_hash.py             # Utility to seed bcrypt hashes
│
├── database_schema/
│   ├── Supershop.sql            # All 21 tables, sequences, triggers, views
│   ├── supabase_views.sql       # Views exposed to Supabase
│   ├── Supershop_Data.sql       # Seed data
│   └── Fixed_Supershop_Query.sql # Lab queries (JOINs, aggregations, triggers)
│
├── templates/                   # Jinja2 SSR
│   ├── storefront.html
│   ├── authentication/          # Single login page — picks Admin / Employee / Customer
│   ├── admin/                   # HQ admin (12 pages)
│   ├── customer/                # Customer (10 pages)
│   ├── employee/                # Role-split: branch_manager · cashier · sales_staff · rider
│   └── errors/
│
├── static/
│   └── js/
│       └── utils.js             
│
├── SuperShop_Bangladesh_Project_Report.pdf        # 📄 Project report
├── SuperShop_Bangladesh_Project_Presentation.pdf  # 🎞️ Presentation slides
│
├── requirements.txt
├── Procfile                      # Heroku/Railway entrypoint (kept for portability)
├── vercel.json                   # Vercel: @vercel/python → main.py
└── README.md
```

---


## 🛠 Troubleshooting

| Problem | Fix |
|---|---|
| `ModuleNotFoundError: fastapi` | Activate the venv first. |
| `address already in use` | `uvicorn main:app --reload --port 8001` |
| Templates not found | Folder must be lowercase `templates/` |
| `.env` values ignored | Ensure `load_dotenv()` runs before any `os.environ` lookup in `database.py` / `supabase_client.py` |
| `psycopg2` install fails | Use `psycopg2-binary` (already in `requirements.txt`) |
| Login doesn't redirect | `SECRET_KEY` is missing or was rotated mid-session |
| Vercel deploy fails | Check Deploy Logs — usually a typo'd `DATABASE_URL` or missing `SECRET_KEY` |
| Product images blank | Confirm `SUPABASE_URL` / `SUPABASE_SERVICE_ROLE_KEY` are set, and the `Images` bucket is public |


---

## 📄 License

MIT — see [`LICENSE`](./LICENSE). Free to use, copy, modify, and distribute.
