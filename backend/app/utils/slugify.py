import re


def slugify(text: str) -> str:
    """Mirrors the frontend's own slugify() in categories.js / sub-categories.js
    so admin-entered slugs and any auto-generated ones stay consistent."""
    text = (text or "").strip().lower()
    text = re.sub(r"[^a-z0-9\s-]", "", text)
    text = re.sub(r"\s+", "-", text)
    text = re.sub(r"-+", "-", text)
    return text.strip("-")