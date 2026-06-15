"""
branch_routes.py  — SuperShop Bangladesh
==========================================
POST routes for the manage_branches.html drawer forms.

Add to main.py:
    from branch_routes import branch_router
    app.include_router(branch_router)
"""

from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import RedirectResponse
from urllib.parse import quote
from database import query, execute
from auth import require_admin
from auth import _hash, _verify
branch_router = APIRouter(prefix="/admin/branches", tags=["Branch Management"])

BACK = "/admin/dashboard/branches/manage"


def redir(msg: str, ok: bool = True) -> RedirectResponse:
    key = "success" if ok else "error"
    return RedirectResponse(f"{BACK}?{key}={quote(msg)}", status_code=302)


# ══════════════════════════════════════════════════════════════════════════════
#  GET: Manage branches page
# ══════════════════════════════════════════════════════════════════════════════

# (route is already in main.py at /admin/dashboard/branches/manage)


# ══════════════════════════════════════════════════════════════════════════════
#  1. ADD CITY
# ══════════════════════════════════════════════════════════════════════════════

@branch_router.post("/city/add")
def add_city(
    request: Request,
    city_id:   str = Form(...),
    city_name: str = Form(...),
    division:  str = Form(...),
    session=Depends(require_admin),
):
    city_id = city_id.strip().upper()

    # Validate format: BD-XXX
    import re
    if not re.match(r'^BD-[A-Z]{3}$', city_id):
        return redir("City ID must match BD-XXX format (e.g. BD-SYL)", ok=False)

    # Check duplicate
    existing = query("SELECT 1 FROM city WHERE city_id = %s", (city_id,))
    if existing:
        return redir(f"City ID '{city_id}' already exists.", ok=False)

    existing_name = query("SELECT 1 FROM city WHERE city_name = %s", (city_name.strip(),))
    if existing_name:
        return redir(f"City '{city_name}' is already registered.", ok=False)

    execute(
        "INSERT INTO city (city_id, city_name, division) VALUES (%s, %s, %s)",
        (city_id, city_name.strip(), division.strip())
    )
    return redir(f"City '{city_name}' ({city_id}) added successfully.")


# ══════════════════════════════════════════════════════════════════════════════
#  2. DELETE CITY
#  Guards: city must have no branches; confirm_name must match
# ══════════════════════════════════════════════════════════════════════════════

@branch_router.post("/city/delete")
def delete_city(
    request: Request,
    city_id:      str = Form(...),
    confirm_name: str = Form(...),
    session=Depends(require_admin),
):
    # Fetch city record
    city = query("SELECT city_id, city_name FROM city WHERE city_name = %s", (city_id,))
    if not city:
        return redir("City not found.", ok=False)

    city_record = city[0]

    # Safety: name confirmation
    if confirm_name.strip() != city_record["city_name"]:
        return redir(
            f"Confirmation failed — you typed '{confirm_name}' "
            f"but the city name is '{city_record['city_name']}'.",
            ok=False
        )

    # Guard: no branches may exist in this city
    branches = query(
        "SELECT COUNT(*) AS n FROM branch WHERE city_id = %s",
        (city_record["city_id"],)
    )
    if branches[0]["n"] > 0:
        return redir(
            f"Cannot delete '{city_record['city_name']}' — "
            f"it has {branches[0]['n']} branch(es). Remove all branches first.",
            ok=False
        )

    execute("DELETE FROM city WHERE city_id = %s", (city_record["city_id"],))
    return redir(f"City '{city_record['city_name']}' deleted.")


# ══════════════════════════════════════════════════════════════════════════════
#  3. ADD NEW BRANCH
# ══════════════════════════════════════════════════════════════════════════════

@branch_router.post("/add")
def add_branch(
    request: Request,
    branch_id:   str = Form(...),
    branch_name: str = Form(...),
    city_id:     str = Form(...),     # this is city_name from the select
    address:     str = Form(...),
    phone:       str = Form(""),
    open_time:   str = Form("09:00"),
    close_time:  str = Form("22:00"),
    is_active:   str = Form("Y"),
    session=Depends(require_admin),
):
    import re
    branch_id = branch_id.strip().upper()

    if not re.match(r'^B-[A-Z0-9]{4}$', branch_id):
        return redir("Branch ID must match B-XXXX format (e.g. B-SY02)", ok=False)

    # Resolve city_id from city_name (since select sends city_name)
    city = query("SELECT city_id FROM city WHERE city_name = %s", (city_id,))
    if not city:
        return redir(f"City '{city_id}' not found.", ok=False)
    real_city_id = city[0]["city_id"]

    existing = query("SELECT 1 FROM branch WHERE branch_id = %s", (branch_id,))
    if existing:
        return redir(f"Branch ID '{branch_id}' already exists.", ok=False)

    if phone.strip():
        dup_phone = query("SELECT 1 FROM branch WHERE phone = %s", (phone.strip(),))
        if dup_phone:
            return redir(f"Phone '{phone.strip()}' is already used by another branch.", ok=False)

    execute(
        """INSERT INTO branch
           (branch_id, branch_name, city_id, address, phone, open_time, close_time, is_active)
           VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
        (
            branch_id, branch_name.strip(), real_city_id,
            address.strip(),
            phone.strip() or None,
            open_time, close_time, is_active
        )
    )
    return redir(f"Branch '{branch_name}' ({branch_id}) created successfully.")


# ══════════════════════════════════════════════════════════════════════════════
#  4. ASSIGN MANAGER
#  Inserts a new row into branch_manager.
#  The DB trigger rejects non-BRANCH_MANAGER employees.
#  If the branch already has a manager, this raises a PK conflict —
#  redirect user to Reassign instead.
# ══════════════════════════════════════════════════════════════════════════════

@branch_router.post("/manager/assign")
def assign_manager(
    request: Request,
    branch_id:   str = Form(...),
    emp_id:      str = Form(...),
    assigned_on: str = Form(""),
    session=Depends(require_admin),
):
    emp_id    = emp_id.strip().upper()
    branch_id = branch_id.strip()

    # Check employee exists and is BRANCH_MANAGER
    emp = query(
        "SELECT emp_id, emp_name, position FROM employee WHERE emp_id = %s",
        (emp_id,)
    )
    if not emp:
        return redir(f"Employee '{emp_id}' not found.", ok=False)

    if emp[0]["position"] != "BRANCH_MANAGER":
        return redir(
            f"{emp[0]['emp_name']} has position '{emp[0]['position']}', "
            f"not BRANCH_MANAGER. Only BRANCH_MANAGER employees can be assigned.",
            ok=False
        )

    # Check if branch already has a manager
    existing_mgr = query(
        "SELECT emp_id FROM branch_manager WHERE branch_id = %s", (branch_id,)
    )
    if existing_mgr:
        return redir(
            "This branch already has a manager. "
            "Use 'Manage Branch Manager → Reassign' to replace them.",
            ok=False
        )

    # Check if this employee is already managing another branch
    already_managing = query(
        "SELECT branch_id FROM branch_manager WHERE emp_id = %s", (emp_id,)
    )
    if already_managing:
        return redir(
            f"{emp[0]['emp_name']} is already the manager of "
            f"branch '{already_managing[0]['branch_id']}'. "
            f"Remove that assignment first.",
            ok=False
        )

    date_val = assigned_on.strip() if assigned_on.strip() else "CURRENT_DATE"

    if assigned_on.strip():
        execute(
            "INSERT INTO branch_manager (branch_id, emp_id, assigned_on) VALUES (%s, %s, %s)",
            (branch_id, emp_id, assigned_on.strip())
        )
        
    else:
        execute(
            "INSERT INTO branch_manager (branch_id, emp_id, assigned_on) VALUES (%s, %s, CURRENT_DATE)",
            (branch_id, emp_id)
        )
    execute(
        "UPDATE employee SET branch_id = %s WHERE emp_id = %s",
        (branch_id, emp_id)
    )

    return redir(f"{emp[0]['emp_name']} assigned as manager of branch '{branch_id}'.")


# ══════════════════════════════════════════════════════════════════════════════
#  5a. REASSIGN MANAGER
#  Replaces existing manager row with a new employee.
# ══════════════════════════════════════════════════════════════════════════════

@branch_router.post("/manager/reassign")
def reassign_manager(
    request: Request,
    branch_id:  str = Form(...),
    new_emp_id: str = Form(...),
    session=Depends(require_admin),
):
    new_emp_id = new_emp_id.strip().upper()
    branch_id  = branch_id.strip()

    # Validate new employee
    emp = query(
        "SELECT emp_id, emp_name, position FROM employee WHERE emp_id = %s",
        (new_emp_id,)
    )
    if not emp:
        return redir(f"Employee '{new_emp_id}' not found.", ok=False)

    if emp[0]["position"] != "BRANCH_MANAGER":
        return redir(
            f"{emp[0]['emp_name']} has position '{emp[0]['position']}', "
            f"not BRANCH_MANAGER.",
            ok=False
        )

    # Check this employee isn't already managing another branch
    already = query(
        "SELECT branch_id FROM branch_manager WHERE emp_id = %s AND branch_id <> %s",
        (new_emp_id, branch_id)
    )
    if already:
        return redir(
            f"{emp[0]['emp_name']} already manages branch '{already[0]['branch_id']}'. "
            f"Remove that assignment first.",
            ok=False
        )

    # Upsert: delete old row + insert new (handles both "already has manager" and "no manager")
    execute("DELETE FROM branch_manager WHERE branch_id = %s", (branch_id,))
    execute(
        "INSERT INTO branch_manager (branch_id, emp_id, assigned_on) VALUES (%s, %s, CURRENT_DATE)",
        (branch_id, new_emp_id)
    )
    execute(
        "UPDATE employee SET branch_id = %s WHERE emp_id = %s",
        (branch_id, new_emp_id)
    )

    return redir(f"{emp[0]['emp_name']} is now the manager of branch '{branch_id}'.")


# ══════════════════════════════════════════════════════════════════════════════
#  5b. REMOVE MANAGER FROM BRANCH
#  Only deletes the branch_manager row — employee record untouched.
#  After this, the employee CAN be deleted from the Employees page.
# ══════════════════════════════════════════════════════════════════════════════
@branch_router.post("/manager/remove")
def remove_manager(
    request: Request,
    branch_id: str = Form(...),
    session=Depends(require_admin),
):
    branch_id = branch_id.strip()

    mgr = query(
        """SELECT bm.emp_id, e.emp_name, b.branch_name
           FROM branch_manager bm
           JOIN employee e ON bm.emp_id = e.emp_id
           JOIN branch b ON bm.branch_id = b.branch_id
           WHERE bm.branch_id = %s""",
        (branch_id,)
    )
    if not mgr:
        return redir(f"Branch '{branch_id}' has no manager assigned.", ok=False)

    emp_id     = mgr[0]["emp_id"]
    emp_name   = mgr[0]["emp_name"]
    branch_name = mgr[0]["branch_name"]

    # Remove from branch_manager table
    execute("DELETE FROM branch_manager WHERE branch_id = %s", (branch_id,))

    # Nullify their home branch — they are unassigned until given a new branch
    execute("UPDATE employee SET branch_id = NULL WHERE emp_id = %s", (emp_id,))

    return redir(
        f"{emp_name} removed as manager of '{branch_name}'. "
        f"Use 'Assign Manager' to reassign them, or go to Employees to update their details."
    )

 
 
def _next_emp_id() -> str:
    """
    Auto-generate the next employee ID in the format E-XXXXX.
    Finds the highest numeric emp_id and increments it.
    Skips non-numeric suffixes like E-R001.
    """
    rows = query("""
        SELECT emp_id FROM employee
        WHERE emp_id ~ '^E-[0-9]+$'
        ORDER BY emp_id DESC
        LIMIT 1
    """)
    if not rows:
        return "E-00001"
    last = rows[0]["emp_id"]          # e.g. "E-00017"
    num  = int(last.split("-")[1]) + 1
    return f"E-{num:05d}"
 
 
def _next_user_id() -> str:
    """Auto-generate next app_user ID."""
    rows = query("""
        SELECT user_id FROM app_user
        ORDER BY user_id DESC
        LIMIT 1
    """)
    if not rows:
        return "U-000001"
    last = rows[0]["user_id"]
    num  = int(last.split("-")[1]) + 1
    return f"U-{num:06d}"
 
 
@branch_router.post("/manager/create")
@branch_router.post("/manager/create")
def create_manager(
    request:          Request,
    emp_name:         str   = Form(...),
    email:            str   = Form(""),
    phone:            str   = Form(...),
    dept_id:          str   = Form(""),       # branch_id removed
    salary:           float = Form(...),
    hire_date:        str   = Form(...),
    gender:           str   = Form(...),
    password:         str   = Form(...),
    confirm_password: str   = Form(...),
    session=Depends(require_admin),
):
    if len(password) < 6:
        return redir("Password must be at least 6 characters.", ok=False)
    if password != confirm_password:
        return redir("Passwords do not match.", ok=False)

    phone = phone.strip()
    email = email.strip().lower() or None

    # Phone check — employee table only (no role column there)
    if query("SELECT 1 FROM employee WHERE phone = %s", (phone,)):
        return redir(f"Phone '{phone}' is already registered to another employee.", ok=False)

    # Phone check — app_user EMPLOYEE role only
    if query("SELECT 1 FROM app_user WHERE phone = %s AND role = 'EMPLOYEE'", (phone,)):
        return redir(f"Phone '{phone}' already has an employee login account.", ok=False)

    if email and query("SELECT 1 FROM employee WHERE email = %s", (email,)):
        return redir(f"Email '{email}' is already registered.", ok=False)

    if salary < 10000:
        return redir(f"Salary must be at least ৳10,000.", ok=False)

    emp_id  = _next_emp_id()
    user_id = _next_user_id()
    pw_hash = _hash(password)

    # branch_id is NULL — will be set when assigned via Assign Manager
    execute("""
        INSERT INTO employee
            (emp_id, emp_name, email, phone, branch_id, dept_id,
             position, salary, hire_date, gender, is_active)
        VALUES (%s, %s, %s, %s, NULL, %s, 'BRANCH_MANAGER', %s, %s, %s, 'Y')
    """, (
        emp_id, emp_name.strip(), email, phone,
        dept_id.strip() or None,
        salary, hire_date, gender,
    ))

    execute("""
        INSERT INTO app_user
            (user_id, phone, password_hash, role, ref_id, is_active, created_at)
        VALUES (%s, %s, %s, 'EMPLOYEE', %s, 'Y', CURRENT_TIMESTAMP)
    """, (user_id, phone, pw_hash, emp_id))

    return redir(
        f"Manager account created for '{emp_name.strip()}' (ID: {emp_id}). "
        f"Now use 'Assign Manager' to link them to a branch."
    )