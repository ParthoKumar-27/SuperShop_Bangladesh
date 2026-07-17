"""SuperShop Bangladesh — FastAPI composition root.

Just wires the bootstrapped `app`, the routers, and the storefront/error
modules together. All heavy logic lives in the sibling modules:
  • app_setup.py        — FastAPI(), middleware, templates, static mount
  • storefront_routes.py — /, /search, hot-deals, image-url helper, ROLE_HOME
  • error_handlers.py   — 403 / 404 handlers, shutdown hook
"""
from admin             import admin_router
from app_setup         import app                              # noqa: F401  (side-effects)
from auth              import auth_router
from branch_routes     import branch_router
from customer          import customer_router
from employee          import employee_router
from error_handlers    import *                                # noqa: F401,F403  (attaches handlers)
from storefront_routes import *                                # noqa: F401,F403  (attaches /, /search)

# ── Routers ────────────────────────────────────────────────────────────────────
app.include_router(auth_router)
app.include_router(branch_router)
app.include_router(customer_router)
app.include_router(admin_router)
app.include_router(employee_router)
