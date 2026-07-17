"""FastAPI app object, middleware, templates, and static mount.

Everything that bootstraps the FastAPI() instance lives here so `main.py`
stays a tiny composition root. The `app` object is exported and imported
by `storefront_routes.py` / `error_handlers.py` so they can attach their
own routes and exception handlers.
"""
import os

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware


# ── App setup ──────────────────────────────────────────────────────────────────
app = FastAPI(
    title="SuperShop Bangladesh",
    description="Multi-branch retail management system",
    version="1.0.0"
)

# ── Session middleware ─────────────────────────────────────────────────────────
app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SECRET_KEY", "change-this-in-production-32chars"),
    max_age=3600 * 8,
    https_only=True,
)


# ── No-cache middleware ────────────────────────────────────────────────────────
# Logout-then-back-button can otherwise restore authenticated pages from the
# browser's bfcache or disk cache. Tell the browser not to cache any HTML
# response; combined with the `pageshow` handler in the templates, this
# forces a hard reload any time the user navigates back to an auth'd page.
class NoCacheHTMLMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                ct = b""
                for k, v in headers:
                    if k == b"content-type":
                        ct = v.lower()
                        break
                # Apply no-cache only to HTML responses — leave JSON / images
                # / CSS / JS untouched so the rest of the site stays fast.
                if ct.startswith(b"text/html"):
                    headers += [
                        (b"cache-control", b"no-store, no-cache, must-revalidate, private"),
                        (b"pragma",        b"no-cache"),
                        (b"expires",       b"0"),
                    ]
                message["headers"] = headers
            await send(message)

        await self.app(scope, receive, send_wrapper)


app.add_middleware(NoCacheHTMLMiddleware)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")
templates.env.filters["sum_cart_qty"] = lambda c: (
    0 if not c else sum(
        (int(v.get("qty", 0)) if isinstance(v, dict) else int(v or 0))
        for v in c.values()
    )
)
