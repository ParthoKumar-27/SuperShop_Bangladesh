"""
auth.py  — SuperShop Bangladesh Authentication
=================================================
Three login paths:
  POST /auth/admin/login      → admin_id + password  → /admin/dashboard
  POST /auth/employee/login   → phone   + password  → /employee/dashboard
  POST /auth/customer/login   → phone   + password  → /customer/dashboard
  POST /auth/customer/register → create new customer + app_user row

Dependencies:  pip install bcrypt python-multipart itsdangerous
Add to main.py: from auth import auth_router; app.include_router(auth_router)
"""

from importlib.resources import path
import os
import re
import uuid
from urllib.parse import quote
import bcrypt

from fastapi import APIRouter, Request, Form, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware    # add to app in main.py
from database import query, execute

# ── Router ─────────────────────────────────────────────────────────────────────
auth_router = APIRouter(prefix="/auth", tags=["Auth"])
templates   = Jinja2Templates(directory="templates")


# ══════════════════════════════════════════════════════════════════════════════
#  HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def _hash(plain: str) -> str:
    """Return bcrypt hash of a plaintext password."""
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


def _verify(plain: str, hashed: str) -> bool:
    """Return True if plaintext matches bcrypt hash."""
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def _redirect_error(path: str, msg: str, identifier: str | None = None) -> RedirectResponse:
    """Redirect to login page with an error message in the query string.

    If ``identifier`` is provided (e.g. admin_id or phone), it is appended
    as ``&id=`` so the form can be pre-filled after the redirect.
    """
    from urllib.parse import quote
    separator = "&" if "?" in path else "?"
    extra = f"&id={quote(identifier)}" if identifier else ""
    return RedirectResponse(
        f"{path}{separator}error={quote(msg)}{extra}",
        status_code=302
    )


def _next_cust_id() -> str:
    """Generate next customer ID like C-00016 (numeric-only MAX)."""
    rows = query("""
        SELECT MAX(CAST(SUBSTRING(cust_id FROM 3) AS INTEGER)) AS mx
        FROM   customer
        WHERE  cust_id ~ '^C-[0-9]+$'
    """)
    mx = rows[0]["mx"] if rows else None
    return f"C-{(mx or 0) + 1:05d}"


def _next_user_id() -> str:
    """Generate next app_user ID like U-000036 (numeric-only MAX)."""
    rows = query("""
        SELECT MAX(CAST(SUBSTRING(user_id FROM 3) AS INTEGER)) AS mx
        FROM   app_user
        WHERE  user_id ~ '^U-[0-9]+$'
    """)
    mx = rows[0]["mx"] if rows else None
    return f"U-{(mx or 0) + 1:06d}"


# ══════════════════════════════════════════════════════════════════════════════
#  LOGIN PAGE  (GET)
# ══════════════════════════════════════════════════════════════════════════════

@auth_router.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    """Serve the login page (login.html)."""
    return templates.TemplateResponse(request, "authentication/login.html", {})


# ══════════════════════════════════════════════════════════════════════════════
#  ADMIN LOGIN
#  Credentials: admin_id (e.g. ADM-001) + password
#  Stored in: admin_account table
# ══════════════════════════════════════════════════════════════════════════════

@auth_router.post("/admin/login")
def admin_login(
    request : Request,
    admin_id : str = Form(...),
    password : str = Form(...)
):
    FAIL = "/auth/login?role=admin"

    rows = query(
        "SELECT admin_id, admin_name, password_hash, is_active "
        "FROM admin_account WHERE admin_id = %s",
        (admin_id.strip(),)
    )

    if not rows:
        return _redirect_error(FAIL, "Admin ID not found.", admin_id)

    admin = rows[0]

    if admin["is_active"] != "Y":
        return _redirect_error(FAIL, "This admin account is inactive.", admin_id)

    if not _verify(password, admin["password_hash"]):
        return _redirect_error(FAIL, "Incorrect password.", admin_id)

    # ── Set session ────────────────────────────────────────────────────────
    request.session["user_id"]   = admin["admin_id"]
    request.session["user_name"] = admin["admin_name"]
    request.session["role"]      = "ADMIN"

    return RedirectResponse("/admin/dashboard", status_code=302)


# ══════════════════════════════════════════════════════════════════════════════
#  EMPLOYEE LOGIN
#  Credentials: phone + password
#  Flow: look up phone in app_user WHERE role='EMPLOYEE'
#        → get ref_id (emp_id) → load employee data
# ══════════════════════════════════════════════════════════════════════════════

@auth_router.post("/employee/login")
def employee_login(
    request  : Request,
    phone    : str = Form(...),
    password : str = Form(...)
):
    FAIL = "/auth/login?role=employee"
    phone = phone.strip()

    rows = query(
        "SELECT user_id, password_hash, ref_id, is_active "
        "FROM app_user WHERE phone = %s AND role = 'EMPLOYEE'",
        (phone,)
    )

    if not rows:
        return _redirect_error(FAIL, "No employee account found for this phone number.", phone)

    user = rows[0]

    if user["is_active"] != "Y":
        return _redirect_error(FAIL, "This employee account is inactive.", phone)

    if not _verify(password, user["password_hash"]):
        return _redirect_error(FAIL, "Incorrect password.", phone)

    # ── Load employee details (branch, position) ───────────────────────────
    emp = query(
        "SELECT emp_id, emp_name, branch_id, position "
        "FROM employee WHERE emp_id = %s",
        (user["ref_id"],)
    )
    if not emp:
        return _redirect_error(FAIL, "Employee record not found. Contact admin.", phone)

    e = emp[0]

    # ── Set session ────────────────────────────────────────────────────────
    request.session["user_id"]   = e["emp_id"]
    request.session["user_name"] = e["emp_name"]
    request.session["role"]      = "EMPLOYEE"
    request.session["branch_id"] = e["branch_id"]
    request.session["position"]  = e["position"]

    if request.session["position"] == "BRANCH_MANAGER":
        return RedirectResponse("/employee/branch/dashboard", status_code=302)
    elif request.session["position"] == "CASHIER":
        return RedirectResponse("/employee/cashier/dashboard", status_code=302)
    elif request.session["position"] == "DELIVERY_RIDER":
        return RedirectResponse("/employee/delivery_rider/dashboard", status_code=302)
    elif request.session["position"] == "SALES_STAFF":
        return RedirectResponse("/employee/sales_staff/dashboard", status_code=302)
    else:
        return RedirectResponse("/employee/dashboard", status_code=302)


# ══════════════════════════════════════════════════════════════════════════════
#  CUSTOMER LOGIN
#  Credentials: phone + password
#  Flow: look up phone in app_user WHERE role='CUSTOMER'
#        → get ref_id (cust_id) → load customer data
# ══════════════════════════════════════════════════════════════════════════════

@auth_router.post("/customer/login")
def customer_login(
    request  : Request,
    phone    : str = Form(...),
    password : str = Form(...)
):
    FAIL = "/auth/login?role=customer"
    phone = phone.strip()

    rows = query(
        "SELECT user_id, password_hash, ref_id, is_active "
        "FROM app_user WHERE phone = %s AND role = 'CUSTOMER'",
        (phone,)
    )

    if not rows:
        # Check if they exist as a ghost customer (enrolled by cashier, no password yet)
        ghost = query("SELECT 1 FROM customer WHERE phone = %s", (phone,))
        if ghost:
            return _redirect_error(
                FAIL,
                "You have shopped with us before! Please register to activate your account and see your loyalty points.",
                phone,
            )
        return _redirect_error(FAIL, "No account found. Please register first.", phone)

    user = rows[0]

    if user["is_active"] != "Y":
        return _redirect_error(FAIL, "Your account is inactive. Contact support.", phone)

    if not _verify(password, user["password_hash"]):
        return _redirect_error(FAIL, "Incorrect password.", phone)

    # ── Load customer details ──────────────────────────────────────────────
    cust = query(
        "SELECT cust_id, cust_name, membership_type, loyalty_points "
        "FROM customer WHERE cust_id = %s",
        (user["ref_id"],)
    )
    if not cust:
        return _redirect_error(FAIL, "Customer record not found. Contact support.", phone)

    c = cust[0]

    # ── Set session ────────────────────────────────────────────────────────
    request.session["user_id"]        = c["cust_id"]
    request.session["user_name"]      = c["cust_name"]
    request.session["role"]           = "CUSTOMER"
    request.session["membership"]     = c["membership_type"]
    request.session["loyalty_points"] = int(c["loyalty_points"])

    return RedirectResponse("/", status_code=302)


# ══════════════════════════════════════════════════════════════════════════════
#  CUSTOMER REGISTRATION
#
#  Three cases handled:
#
#  Case 1 — Brand new customer (never visited):
#    Phone not in customer table → create customer + app_user normally.
#
#  Case 2 — Ghost customer (enrolled by cashier, has customer row, no app_user):
#    Phone exists in customer but NOT in app_user →
#    Just create the app_user linked to the existing cust_id.
#    Their loyalty points and purchase history carry over automatically.
#
#  Case 3 — Already fully registered (customer + app_user both exist):
#    Block with a friendly "already registered, please log in" message.
# ══════════════════════════════════════════════════════════════════════════════

@auth_router.post("/customer/register")
def customer_register(
    request   : Request,
    cust_name : str = Form(...),
    phone     : str = Form(...),
    email     : str = Form(...),
    password  : str = Form(...),
    gender    : str = Form("M"),
    address   : str = Form(""),
):
    FAIL = "/auth/login?role=customer"
    phone = phone.strip()
    email = email.strip().lower()

    # ── Basic validation ───────────────────────────────────────────────────
    if len(password) < 6:
        return _redirect_error(FAIL, "Password must be at least 6 characters.")

    # ── Check if a login already exists for this phone ─────────────────────
    existing_user = query(
        "SELECT user_id FROM app_user WHERE phone = %s AND role = 'CUSTOMER'",
        (phone,)
    )
    if existing_user:
        return _redirect_error(
            FAIL,
            "This phone number is already registered. Please log in instead."
        )

    # ── Check if email is already taken (by any customer) ─────────────────
    if email:
        existing_email = query(
            "SELECT 1 FROM customer WHERE email = %s", (email,)
        )
        if existing_email:
            return _redirect_error(FAIL, "This email is already in use.")

    # ── Case 2: Ghost customer — phone exists in customer but no app_user ──
    ghost = query(
        "SELECT cust_id, cust_name, loyalty_points, membership_type "
        "FROM customer WHERE phone = %s",
        (phone,)
    )

    if ghost:
        # Claim the existing customer record
        existing_cust = ghost[0]
        cust_id = existing_cust["cust_id"]

        # Update their name, email, address, gender now that they've registered
        execute("""
            UPDATE customer
            SET  cust_name = %s,
                 email     = %s,
                 address   = %s,
                 gender    = %s
            WHERE cust_id  = %s
        """, (
            cust_name.strip(),
            email or None,
            address.strip() or None,
            gender,
            cust_id,
        ))

        # Create the app_user login
        user_id = _next_user_id()
        execute("""
            INSERT INTO app_user
                (user_id, phone, password_hash, role, ref_id, is_active, created_at)
            VALUES (%s, %s, %s, 'CUSTOMER', %s, 'Y', CURRENT_TIMESTAMP)
        """, (user_id, phone, _hash(password), cust_id))

        # Do NOT auto-login. Instead, show a success popup on the login page.
        return RedirectResponse(
            "/auth/login?role=customer&registered=1"
            f"&welcome=1"
            f"&name={quote(cust_name.strip())}"
            f"&phone={quote(phone)}"
            f"&points={existing_cust['loyalty_points']}",
            status_code=302,
        )

    # ── Case 1: Brand new customer — create everything fresh ───────────────
    cust_id = _next_cust_id()
    user_id = _next_user_id()
    pw_hash = _hash(password)

    execute("""
        INSERT INTO customer
            (cust_id, cust_name, email, phone, address, gender,
             join_date, loyalty_points, membership_type)
        VALUES (%s, %s, %s, %s, %s, %s, CURRENT_DATE, 0, 'REGULAR')
    """, (cust_id, cust_name.strip(), email or None, phone, address.strip() or None, gender))

    execute("""
        INSERT INTO app_user
            (user_id, phone, password_hash, role, ref_id, is_active, created_at)
        VALUES (%s, %s, %s, 'CUSTOMER', %s, 'Y', CURRENT_TIMESTAMP)
    """, (user_id, phone, pw_hash, cust_id))

    # Do NOT auto-login. Redirect back to login with a success flag so the
    # page can display a "Registration successful" popup and ask the user
    # to sign in with their new credentials.
    return RedirectResponse(
        "/auth/login?role=customer&registered=1"
        f"&name={quote(cust_name.strip())}"
        f"&phone={quote(phone)}",
        status_code=302,
    )


# ══════════════════════════════════════════════════════════════════════════════
#  LOGOUT
# ══════════════════════════════════════════════════════════════════════════════

@auth_router.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/auth/login", status_code=302)


# ══════════════════════════════════════════════════════════════════════════════
#  SESSION DEPENDENCY  (use in protected routes)
# ══════════════════════════════════════════════════════════════════════════════

def require_admin(request: Request):
    """FastAPI dependency — protects admin-only routes."""
    if request.session.get("role") != "ADMIN":
        raise HTTPException(status_code=403, detail="Admin access required.")
    return request.session

def require_employee(request: Request):
    """FastAPI dependency — protects employee routes."""
    if request.session.get("role") not in ("ADMIN", "EMPLOYEE"):
        raise HTTPException(status_code=403, detail="Employee access required.")
    return request.session

def require_customer(request: Request):
    """FastAPI dependency — protects customer routes."""
    if request.session.get("role") != "CUSTOMER":
        raise HTTPException(status_code=403, detail="Please log in as a customer.")
    return request.session

def require_login(request: Request):
    """FastAPI dependency — any authenticated user."""
    if not request.session.get("role"):
        raise HTTPException(status_code=401, detail="Login required.")
    return request.session