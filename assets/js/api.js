/* ==========================================================================
   API.JS — Badariya Flowers Website · Centralized API Configuration
   ----------------------------------------------------------------------
   ONE place that knows the FastAPI base URL for the public website.
   catalog.js (and any future site script) calls Api.get(...) instead of
   hardcoding fetch() URLs. Keep this file's API_BASE in sync with
   admin/assets/js/api.js — same backend, two copies because the project
   has no build step to share one file between /assets and /admin/assets.

   Local development points at the FastAPI dev server. When you deploy,
   change ONLY the line below.
   ========================================================================== */

// const API_BASE = "https://badariya-flowers.onrender.com/api";
// const API_ORIGIN = API_BASE.replace(/\/api\/?$/, "");

const API_BASE =
  window.location.hostname === "127.0.0.1" ||
  window.location.hostname === "localhost"
    ? "http://127.0.0.1:8000/api"
    : "/api";

const API_ORIGIN = API_BASE.replace(/\/api\/?$/, "");
/** Resolves a relative "/uploads/…" URL from the backend into an absolute one. */
function mediaUrl(path) {
  if (!path) return path;
  if (/^(https?:)?\/\//i.test(path) || path.startsWith("data:")) return path;
  return API_ORIGIN + path;
}

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
  const res = await fetch(url, { method: options.method || "GET" });
  const text = await res.text();
  let body = null;
  if (text) { try { body = JSON.parse(text); } catch (e) { /* non-JSON */ } }
  if (!res.ok) {
    throw new Error((body && body.message) || `Request failed (${res.status})`);
  }
  return body;
}

const Api = {
  get(path, query) { return apiFetch(path, { method: "GET", query }); },
};

window.Api = Api;
window.API_BASE = API_BASE;
window.API_ORIGIN = API_ORIGIN;
window.mediaUrl = mediaUrl;
