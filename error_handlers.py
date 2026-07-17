"""Global exception handlers + shutdown hook.

These attach themselves to the shared `app` instance imported from
`app_setup.py`. The 403 handler depends on `ROLE_HOME`, which lives in
`storefront_routes.py` — import it from there so there is one source of
truth.
"""
import urllib.parse

from fastapi import Request
from fastapi.responses import HTMLResponse
from starlette.responses import RedirectResponse

from app_setup import app, templates
from database import close_pool
from storefront_routes import ROLE_HOME


@app.exception_handler(403)
async def _forbidden_handler(request: Request, exc):
    """Auth failure handler.

    - Anonymous users  → redirect to login (with ?next=<original>).
    - Logged-in users who URL-edit into a page they're not allowed to
      access (admin → employee URL, employee → other employee/admin URL,
      etc.) → the user stays on the page they were already viewing.
      We return a tiny invisible HTML page that immediately runs
      `history.back()` so the browser snaps back to where they came from,
      leaving the URL bar pointing at *their* dashboard (not the forbidden
      URL they typed). No new page is rendered.
    """
    sess = getattr(request, "session", {}) or {}
    role = sess.get("role")

    # ── Anonymous: must log in first ────────────────────────────────────────
    if not role:
        path = request.url.path or "/"
        qs   = request.url.query or ""
        next_url = f"{path}?{qs}" if qs else path
        return RedirectResponse(
            url=f"/auth/login?next={urllib.parse.quote(next_url, safe='/')}",
            status_code=302,
        )

    # ── Already logged in: bounce silently back to the page they came from ──
    # Returning status 403 keeps it from being cached; the inline <script>
    # navigates back before the user sees anything.
    back_url = request.headers.get("referer") or ROLE_HOME.get(role, "/")
    safe = urllib.parse.quote(back_url, safe="/:?&=")
    body = (
        "<!doctype html><html><head><meta charset='utf-8'>"
        "<style>html,body{margin:0;background:#f8faf9}</style>"
        "<script>history.back();setTimeout(function(){location.replace("
        f"{repr(safe)}"
        ")},50);</script></head><body></body></html>"
    )
    return HTMLResponse(content=body, status_code=403)


@app.exception_handler(404)
async def _not_found_handler(request: Request, exc):
    """Render a friendly 404 page (we don't want the default Starlette plain text)."""
    role = request.session.get("role") if hasattr(request, "session") else None
    return templates.TemplateResponse(
        request,
        "errors/404.html",
        {
            "request_path":  request.url.path,
            "role":          role,
            "is_logged_in":  bool(role),
        },
        status_code=404,
    )


@app.on_event("shutdown")
def shutdown():
    close_pool()
