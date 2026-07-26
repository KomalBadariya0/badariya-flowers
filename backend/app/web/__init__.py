"""
app.web — server-rendered admin pages (Jinja2 + HTMX).

This package is intentionally separate from app.api:
  - app.api.*   -> unchanged JSON REST endpoints (still used by anything
                   that needs raw JSON, kept for backward compatibility).
  - app.web.*   -> HTML endpoints that render full pages or small HTML
                   fragments for HTMX to swap into the page. These call
                   the exact same app.services.* functions as app.api,
                   so business logic / validation / DB access is never
                   duplicated — only the response shape differs
                   (Jinja2 HTML instead of a Pydantic JSON model).
"""
