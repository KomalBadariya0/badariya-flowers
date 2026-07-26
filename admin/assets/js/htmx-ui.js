/* ==========================================================================
   HTMX-UI.JS — Badariya Flowers Admin · shared HTMX glue
   --------------------------------------------------------------------------
   This file replaces the old per-module *.js files (categories.js, etc.)
   for anything that used to be hand-written fetch()/render() logic. It is
   deliberately generic and tiny — every module's Add/Edit/Delete/Search/
   Filter/Toggle behaviour now lives in HTMX attributes in the Jinja2
   templates, not in JS. This file only does three small, reusable things:

     1. Generic modal open/close
        Any element with [data-open-modal="someModalId"] opens that modal
        on click. Any element with [data-close-modal] closes its nearest
        ".cat-modal-overlay" (or "[class$='-overlay']" for future modules).
        Clicking the backdrop itself, or pressing ESC, also closes.

     2. Toast + modal-close driven by the server
        Routes in app/web/*.py send an `HX-Trigger` response header like
        {"toast": {"message": "...", "type": "success"}} and/or
        {"closeModal": {"id": "categoryFormModal"}}. HTMX turns those into
        real CustomEvents on <body> — this file just listens for them.

     3. window.bfSlugify(text)
        One tiny helper reused by inline oninput= handlers in
        category_form.html for the live slug preview as you type the
        category name (a client-only cosmetic touch — the slug is always
        re-validated server-side on Save).
   ========================================================================== */

   (function () {

    /* ---- 1. modal open/close (event delegation, works for content
       swapped in later by HTMX too) ---- */
    document.addEventListener("click", function (e) {
      const openBtn = e.target.closest("[data-open-modal]");
      if (openBtn) {
        const modal = document.getElementById(openBtn.getAttribute("data-open-modal"));
        if (modal) {
          modal.classList.add("is-open");
          document.body.style.overflow = "hidden";
        }
      }
  
      const closeBtn = e.target.closest("[data-close-modal]");
      if (closeBtn) {
        const modal = closeBtn.closest(".cat-modal-overlay");
        if (modal) {
          modal.classList.remove("is-open");
          document.body.style.overflow = "";
        }
      }
  
      // backdrop click (clicking the dimmed overlay itself, not its content)
      if (e.target.classList && e.target.classList.contains("cat-modal-overlay")) {
        e.target.classList.remove("is-open");
        document.body.style.overflow = "";
      }
    });
  
    document.addEventListener("keydown", function (e) {
      if (e.key !== "Escape") return;
      document.querySelectorAll(".cat-modal-overlay.is-open").forEach(function (m) {
        m.classList.remove("is-open");
      });
      document.body.style.overflow = "";
    });
  
    /* ---- 2. server-driven toast + modal close (via HX-Trigger header) ---- */
    document.body.addEventListener("toast", function (e) {
      const toast = document.getElementById(e.detail.toastId || "categoryToast");
      if (!toast) return;
      const msgEl = toast.querySelector("span") || toast;
      msgEl.textContent = e.detail.message;
      toast.classList.remove("is-error", "is-success");
      toast.classList.add(e.detail.type === "error" ? "is-error" : "is-success");
      toast.classList.add("is-open");
      clearTimeout(toast._hideTimer);
      toast._hideTimer = setTimeout(function () { toast.classList.remove("is-open"); }, 2600);
    });
  
    document.body.addEventListener("closeModal", function (e) {
      const modal = document.getElementById(e.detail.id);
      if (modal) {
        modal.classList.remove("is-open");
        document.body.style.overflow = "";
      }
    });
  
    /* ---- 3. slug helper (mirrors the old categories.js slugify() 1:1) ---- */
    window.bfSlugify = function (text) {
      return (text || "")
        .toString().trim().toLowerCase()
        .replace(/[^a-z0-9\s-]/g, "")
        .replace(/\s+/g, "-")
        .replace(/-+/g, "-")
        .replace(/^-|-$/g, "");
    };
  
    /* ---- 4. Product form: tab switching. Buttons carry data-prod-tab="id",
       panels carry data-prod-panel="id", both siblings under #productFormFields. ---- */
    document.addEventListener("click", function (e) {
      const tabBtn = e.target.closest("[data-prod-tab]");
      if (!tabBtn) return;
      const tabsWrap = tabBtn.closest(".prod-tabs");
      const scope = tabsWrap.parentElement; // #productFormFields — holds the sibling panels too
      tabsWrap.querySelectorAll("[data-prod-tab]").forEach(function (b) { b.classList.remove("is-active"); });
      tabBtn.classList.add("is-active");
      scope.querySelectorAll("[data-prod-panel]").forEach(function (p) { p.classList.remove("is-active"); });
      const target = scope.querySelector('[data-prod-panel="' + tabBtn.getAttribute("data-prod-tab") + '"]');
      if (target) target.classList.add("is-active");
    });

    /* ---- 5. Product form: tag chips. Enter/comma in the text entry
       (marked [data-prod-tag-entry]) turns the text into a chip with its
       own hidden name="tags" input; [data-prod-remove-chip] removes one. ---- */
    document.addEventListener("keydown", function (e) {
      if (!e.target.hasAttribute("data-prod-tag-entry")) return;
      if (e.key !== "Enter" && e.key !== ",") return;
      e.preventDefault();
      const val = e.target.value.trim().replace(/,$/, "");
      e.target.value = "";
      if (!val) return;
      const chip = document.createElement("span");
      chip.className = "prod-tag-chip";
      chip.innerHTML = val + ' <input type="hidden" name="tags" value="' + val.replace(/"/g, "&quot;") + '">' +
        '<button type="button" data-prod-remove-chip aria-label="Remove tag"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M6 6l12 12M18 6L6 18"/></svg></button>';
      e.target.parentElement.insertBefore(chip, e.target);
    });
    document.addEventListener("click", function (e) {
      const btn = e.target.closest("[data-prod-remove-chip]");
      if (!btn) return;
      btn.closest(".prod-tag-chip").remove();
    });

    /* ---- 6. Product form: dynamic Specifications / Features rows.
       [data-prod-add-spec] / [data-prod-add-feature] append a new empty
       row into the nearest .prod-list-builder; [data-prod-remove-row]
       removes its own row. ---- */
    document.addEventListener("click", function (e) {
      const addSpec = e.target.closest("[data-prod-add-spec]");
      const addFeature = e.target.closest("[data-prod-add-feature]");
      if (addSpec) {
        const list = addSpec.previousElementSibling;
        const row = document.createElement("div");
        row.className = "prod-list-row";
        row.innerHTML = '<input type="text" name="specLabel" placeholder="Label, e.g. Size">' +
          '<input type="text" name="specValue" placeholder="Value, e.g. 3 Feet">' +
          '<button type="button" class="prod-list-remove-btn" data-prod-remove-row aria-label="Remove specification"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M3 6h18M8 6V4a1 1 0 011-1h6a1 1 0 011 1v2m3 0l-1 14a2 2 0 01-2 2H7a2 2 0 01-2-2L4 6"/></svg></button>';
        list.appendChild(row);
      } else if (addFeature) {
        const list = addFeature.previousElementSibling;
        const row = document.createElement("div");
        row.className = "prod-list-row";
        row.innerHTML = '<input type="text" name="features" placeholder="e.g. Handcrafted with real thread">' +
          '<button type="button" class="prod-list-remove-btn" data-prod-remove-row aria-label="Remove feature"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M3 6h18M8 6V4a1 1 0 011-1h6a1 1 0 011 1v2m3 0l-1 14a2 2 0 01-2 2H7a2 2 0 01-2-2L4 6"/></svg></button>';
        list.appendChild(row);
      }
      const removeRow = e.target.closest("[data-prod-remove-row]");
      if (removeRow) removeRow.closest(".prod-list-row").remove();
    });

    /* ---- 7. Product form: remove a gallery image thumbnail. ---- */
    document.addEventListener("click", function (e) {
      const btn = e.target.closest("[data-prod-remove-image]");
      if (!btn) return;
      btn.closest(".prod-gallery-item").remove();
      bfRefreshGalleryCover();
    });

    /* ---- 8. Product form: live SEO preview. Typing the product name,
       SEO title/description/slug updates the little search-result-style
       preview card — purely cosmetic, server always re-validates on Save. ---- */
    window.bfUpdateSeoPreview = function () {
      const nameEl = document.getElementById("productName");
      const titleEl = document.getElementById("productSeoTitle");
      const descEl = document.getElementById("productSeoDesc");
      const slugEl = document.getElementById("productSeoSlug");
      const shortDescEl = document.getElementById("productShortDesc");
      const pTitle = document.getElementById("productSeoPreviewTitle");
      const pDesc = document.getElementById("productSeoPreviewDesc");
      const pSlug = document.getElementById("productSeoPreviewSlug");
      if (pTitle) pTitle.textContent = (titleEl && titleEl.value) || (nameEl && nameEl.value) || "Product title";
      if (pDesc) pDesc.textContent = (descEl && descEl.value) || (shortDescEl && shortDescEl.value) || "Product description preview appears here.";
      if (pSlug) pSlug.textContent = (slugEl && slugEl.value) || "product-slug";
    };
    document.addEventListener("input", function (e) {
      if (e.target.id === "productName" || e.target.hasAttribute("data-prod-seo-field")) {
        window.bfUpdateSeoPreview();
      }
    });

    /* ---- 9. Product form: gallery — keep the "Cover" badge on whichever
       thumbnail is currently first (after uploads, removals, or a drag
       reorder), and let images be dragged to reorder (order of the hidden
       name="images" inputs is what gets saved). ---- */
    function bfRefreshGalleryCover() {
      const grid = document.getElementById("productGalleryGrid");
      if (!grid) return;
      grid.querySelectorAll(".prod-gallery-item").forEach(function (item, idx) {
        let badge = item.querySelector(".prod-gallery-cover-badge");
        if (idx === 0) {
          if (!badge) {
            badge = document.createElement("span");
            badge.className = "prod-gallery-cover-badge";
            badge.textContent = "Cover";
            item.insertBefore(badge, item.firstChild);
          }
        } else if (badge) {
          badge.remove();
        }
      });
    }
    window.bfRefreshGalleryCover = bfRefreshGalleryCover;

    document.body.addEventListener("htmx:afterSwap", function (e) {
      if (e.target && e.target.id === "productGalleryGrid") bfRefreshGalleryCover();
    });

    /* ---- 10. Settings: live Google Maps preview. Reads whichever of
       #settingsGoogleMapsEmbed (a pasted <iframe> embed code, or an
       already-embeddable URL) or #settingsMapLink (a plain Google Maps
       share link) has a usable value, turns it into a real embeddable
       src (no API key needed — uses Google's documented output=embed
       trick for plain links), and updates the preview iframe live. ---- */
    function bfBuildMapEmbedSrc(raw) {
      if (!raw) return "";
      raw = raw.trim();
      if (!raw) return "";

      // Pasted a full <iframe ... src="...">  code — use its src as-is.
      var iframeSrcMatch = raw.match(/src=["']([^"']+)["']/i);
      if (iframeSrcMatch) return iframeSrcMatch[1];

      // Already an embeddable URL.
      if (/\/maps\/embed/i.test(raw) || /[?&]output=embed/i.test(raw)) return raw;

      // A normal Google Maps URL — pull out a query, place name, or
      // lat/lng and rebuild it in the embeddable "output=embed" form.
      if (/^https?:\/\//i.test(raw)) {
        try {
          var url = new URL(raw);
          var q = url.searchParams.get("q");
          if (q) return "https://www.google.com/maps?q=" + encodeURIComponent(q) + "&output=embed";

          var placeMatch = raw.match(/\/maps\/place\/([^/@]+)/i);
          if (placeMatch) {
            var place = decodeURIComponent(placeMatch[1].replace(/\+/g, " "));
            return "https://www.google.com/maps?q=" + encodeURIComponent(place) + "&output=embed";
          }

          var atMatch = raw.match(/@(-?\d+\.\d+),(-?\d+\.\d+)/);
          if (atMatch) return "https://www.google.com/maps?q=" + atMatch[1] + "," + atMatch[2] + "&output=embed";

          // Shortened links (maps.app.goo.gl, goo.gl/maps) and any other
          // recognised Maps host — best effort, let it try to embed.
          return raw;
        } catch (e) {
          return raw;
        }
      }

      // Not a URL at all — treat it as a plain address/place name typed
      // directly and build a searchable embed from it.
      return "https://www.google.com/maps?q=" + encodeURIComponent(raw) + "&output=embed";
    }

    window.bfUpdateMapPreview = function () {
      var frame = document.getElementById("settingsMapFrame");
      var wrap = document.getElementById("settingsMapPreview");
      if (!frame || !wrap) return;
      var embedEl = document.getElementById("settingsGoogleMapsEmbed");
      var linkEl = document.getElementById("settingsMapLink");
      var raw = (embedEl && embedEl.value.trim()) || (linkEl && linkEl.value.trim()) || "";
      var src = bfBuildMapEmbedSrc(raw);
      if (src) {
        if (frame.getAttribute("data-src") !== src) {
          frame.src = src;
          frame.setAttribute("data-src", src);
        }
        wrap.classList.add("has-map");
      } else {
        frame.removeAttribute("src");
        frame.removeAttribute("data-src");
        wrap.classList.remove("has-map");
      }
    };
    document.addEventListener("input", function (e) {
      if (e.target && e.target.hasAttribute("data-set-map-source")) window.bfUpdateMapPreview();
    });
    // Initial render on first load and again after every HTMX swap of the
    // settings form (e.g. after Save re-renders the fragment).
    document.addEventListener("DOMContentLoaded", window.bfUpdateMapPreview);
    document.body.addEventListener("htmx:afterSwap", function (e) {
      if (e.target && e.target.id === "settingsFormFields") window.bfUpdateMapPreview();
    });

    (function setupGalleryDragReorder() {
      let dragged = null;
      document.addEventListener("dragstart", function (e) {
        const item = e.target.closest(".prod-gallery-item");
        if (!item) return;
        dragged = item;
        e.dataTransfer.effectAllowed = "move";
      });
      document.addEventListener("dragover", function (e) {
        const item = e.target.closest(".prod-gallery-item");
        if (!item || !dragged || item === dragged) return;
        e.preventDefault();
        const grid = item.parentElement;
        const items = Array.from(grid.querySelectorAll(".prod-gallery-item"));
        if (items.indexOf(dragged) < items.indexOf(item)) {
          grid.insertBefore(dragged, item.nextSibling);
        } else {
          grid.insertBefore(dragged, item);
        }
      });
      document.addEventListener("dragend", function () {
        dragged = null;
        bfRefreshGalleryCover();
      });
    })();
  
  })();