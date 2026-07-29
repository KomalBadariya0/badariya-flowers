/* ==========================================================================
   API.JS — Badariya Flowers Admin · Centralized API Configuration
   ----------------------------------------------------------------------
   ONE place that knows the FastAPI base URL. Every admin module
   (categories.js, sub-categories.js, product_store.js, settings.js,
   catalogue.js) calls the helpers below instead of hardcoding fetch()
   URLs anywhere else.

   Local development points at the FastAPI dev server. When you deploy,
   change ONLY the line below — nothing else in the project needs to
   change.
   ========================================================================== */

// const API_BASE = "http://127.0.0.1:8000/api";

// Origin (no /api, no trailing slash) — used to resolve relative
// "/uploads/…" URLs returned by the backend into absolute <img>/<a> URLs.
// const API_ORIGIN = API_BASE.replace(/\/api\/?$/, "");

const API_BASE =
  window.location.hostname === "127.0.0.1" ||
  window.location.hostname === "localhost"
    ? "http://127.0.0.1:8000/api"
    : "/api";

const API_ORIGIN = API_BASE.replace(/\/api\/?$/, "");

/**
 * Resolves a possibly-relative media URL (e.g. "/uploads/products/x.png")
 * returned by the backend into an absolute URL the browser can load.
 * Absolute URLs (http/https), data: URLs, and empty values pass through
 * unchanged.
 */
function mediaUrl(path) {
  if (!path) return path;
  if (/^(https?:)?\/\//i.test(path) || path.startsWith("data:")) return path;
  return API_ORIGIN + path;
}

class ApiError extends Error {
  constructor(message, field, status) {
    super(message);
    this.field = field;
    this.status = status;
  }
}

/**
 * Low-level fetch wrapper.
 *  - path: e.g. "/categories" or "/categories/5"
 *  - options.json: plain object body -> sent as application/json
 *  - options.formData: FormData body -> sent as multipart (no JSON header)
 *  - options.query: plain object -> appended as a query string
 * Throws ApiError with .message / .field (validation) / .status on failure,
 * matching the shape the existing admin UI code already expects
 * (err.message, err.field) from the old localStorage-backed XxxAPI layer.
 */
async function apiFetch(path, options = {}) {
  let url = API_BASE + path;
  if (options.query) {
    const params = new URLSearchParams();
    Object.entries(options.query).forEach(([k, v]) => {
      if (v !== undefined && v !== null && v !== "" && v !== "all") params.set(k, v);
    });
    const qs = params.toString();
    if (qs) url += (url.includes("?") ? "&" : "?") + qs;
  }

  const fetchOptions = { method: options.method || "GET", headers: {} };

  if (options.formData) {
    fetchOptions.body = options.formData; // browser sets multipart boundary
  } else if (options.json !== undefined) {
    fetchOptions.headers["Content-Type"] = "application/json";
    fetchOptions.body = JSON.stringify(options.json);
  }

  let res;
  try {
    res = await fetch(url, fetchOptions);
  } catch (networkErr) {
    throw new ApiError("Could not reach the server. Is the backend running?");
  }

  let body = null;
  const text = await res.text();
  if (text) {
    try { body = JSON.parse(text); } catch (e) { /* non-JSON response */ }
  }

  if (!res.ok) {
    // FastAPI validation errors: { success:false, message:"Validation Error", detail:[{loc:[...],msg:...}] }
    // FastAPI HTTPException errors: { success:false, message:"..." }
    let message = (body && body.message) || `Request failed (${res.status})`;
    let field;
    if (body && Array.isArray(body.detail) && body.detail.length) {
      const first = body.detail[0];
      message = first.msg || message;
      const loc = first.loc || [];
      field = loc[loc.length - 1];
    }
    throw new ApiError(message, field, res.status);
  }

  return body;
}

const Api = {
  get(path, query) { return apiFetch(path, { method: "GET", query }); },
  post(path, json) { return apiFetch(path, { method: "POST", json }); },
  put(path, json) { return apiFetch(path, { method: "PUT", json }); },
  del(path) { return apiFetch(path, { method: "DELETE" }); },
  upload(path, formData) { return apiFetch(path, { method: "POST", formData }); },
};

window.Api = Api;
window.API_BASE = API_BASE;
window.API_ORIGIN = API_ORIGIN;
window.mediaUrl = mediaUrl;
