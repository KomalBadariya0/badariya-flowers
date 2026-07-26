/* ==========================================================================
   MAIN.JS — header, footer, search, WhatsApp helpers (shared every page)
   ========================================================================== */

const ICONS = {
  search: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="11" cy="11" r="7"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>',
  cart: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="9" cy="21" r="1"/><circle cx="20" cy="21" r="1"/><path d="M1 1h4l2.68 13.39a2 2 0 0 0 2 1.61h9.72a2 2 0 0 0 2-1.61L23 6H6"/></svg>',
  call: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 16.9v2a2 2 0 01-2.2 2 19.8 19.8 0 01-8.6-3.1 19.5 19.5 0 01-6-6A19.8 19.8 0 012.1 4.2 2 2 0 014.1 2h2a2 2 0 012 1.7c.1.9.3 1.8.6 2.7a2 2 0 01-.5 2.1L7 9.7a16 16 0 006 6l1.2-1.2a2 2 0 012.1-.5c.9.3 1.8.5 2.7.6a2 2 0 011.7 2z"/></svg>',
  back: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="19" y1="12" x2="5" y2="12"/><polyline points="12 19 5 12 12 5"/></svg>',
  whatsapp: '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M17.5 14.4c-.3-.1-1.7-.9-2-1-.3-.1-.5-.1-.7.1-.2.3-.8 1-.9 1.1-.2.2-.3.2-.6.1-.3-.1-1.2-.4-2.3-1.4-.9-.8-1.4-1.7-1.6-2-.2-.3 0-.5.1-.6.1-.1.3-.3.4-.5.1-.1.2-.3.3-.5.1-.2 0-.4 0-.5C10.1 9 9.6 7.7 9.4 7.2c-.2-.5-.4-.4-.6-.4h-.5c-.2 0-.5.1-.7.3-.2.3-.9.9-.9 2.2s1 2.6 1.1 2.7c.1.2 2 3 4.8 4.2.7.3 1.2.5 1.6.6.7.2 1.3.2 1.8.1.6-.1 1.7-.7 1.9-1.3.2-.7.2-1.2.2-1.3-.1-.1-.3-.2-.6-.3z"/><path d="M12 2C6.5 2 2 6.5 2 12c0 1.9.5 3.7 1.5 5.3L2 22l4.8-1.5c1.5.9 3.3 1.3 5.2 1.3 5.5 0 10-4.5 10-10S17.5 2 12 2zm0 18.1c-1.7 0-3.3-.5-4.7-1.3l-.3-.2-3.2 1 1-3.1-.2-.3C3.6 15 3 13.5 3 12c0-5 4-9 9-9s9 4 9 9-4 9-9 9z"/></svg>',
  pdf: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>',
  arrow: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/></svg>',
  close: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>',
  chevronLeft: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="15 18 9 12 15 6"/></svg>',
  trash: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14a2 2 0 01-2 2H8a2 2 0 01-2-2L5 6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2"/></svg>'
};

function esc(s){ return String(s).replace(/[&<>"']/g, m => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m])); }

/* ---------- WhatsApp message builders ---------- */
function waProductLink(p){
  const lines = [
    `Hello ${SITE.brand},`,
    `I'm interested in this product:`,
    ``,
    `*${p.name}*`,
    p.sku ? `SKU: ${p.sku}` : null,
    `Price: ${p.priceLabel}`,
    `Link: ${location.origin}${location.pathname.replace(/[^/]+$/,'')}product.html?sub=${p.subId}&no=${p.no}`,
    ``,
    `Please share availability.`
  ].filter(Boolean);
  return `https://wa.me/${SITE.whatsappNumber}?text=${encodeURIComponent(lines.join("\n"))}`;
}

function waGeneralLink(){
  const text = encodeURIComponent(`Hello ${SITE.brand}, I'd like to know more about your products.`);
  return `https://wa.me/${SITE.whatsappNumber}?text=${text}`;
}

function waOrderLink(customerName, customerPhone, message){
  const items = cartItems();
  const lines = [
    `Hello ${SITE.brand}, I'd like to place an order.`,
    ``,
    `*Customer Name:* ${customerName}`,
    `*Phone:* ${customerPhone}`,
    ``,
    `*Order Items:*`
  ];
  items.forEach((item, i) => {
    const p = item.product;
    lines.push(`${i + 1}. ${p.name} (SKU: ${p.sku || "N/A"})`);
    lines.push(`   Qty: ${item.qty} x ${p.priceLabel} = ${item.lineTotal != null ? "₹" + item.lineTotal : "Ask for price"}`);
    lines.push(`   Link: ${location.origin}${location.pathname.replace(/[^/]+$/,'')}product.html?sub=${p.subId}&no=${p.no}`);
  });
  lines.push(``);
  lines.push(`*Grand Total: ₹${cartTotal()}*`);
  if(message) { lines.push(``); lines.push(`Note: ${message}`); }
  return `https://wa.me/${SITE.whatsappNumber}?text=${encodeURIComponent(lines.join("\n"))}`;
}

/* ---------- Header ---------- */
function renderHeader(){
  const el = document.getElementById("siteHeader");
  if(!el) return;
  const isHome = document.body.dataset.page === "home";
  el.innerHTML = `
    <div class="container header-row">
      ${!isHome ? `<button class="icon-btn header-back" id="backBtn" aria-label="Go back">${ICONS.chevronLeft}</button>` : ""}
      <a href="/" class="brand-link">
        <img src="${SITE.logo}" alt="${SITE.brand} logo" class="brand-logo">
        <span class="brand-name">${SITE.brand}</span>
      </a>
      <div class="header-actions">
        <button class="icon-btn" id="searchBtn" aria-label="Search">${ICONS.search}</button>
        <a class="icon-btn" href="tel:${SITE.phone.replace(/\s/g,'')}" aria-label="Call us">${ICONS.call}</a>
        <a class="icon-btn cart-icon-btn" href="/cart" aria-label="View cart">
          ${ICONS.cart}
          <span class="cart-badge" data-cart-badge>0</span>
        </a>
      </div>
    </div>`;
  const backBtn = document.getElementById("backBtn");
  if(backBtn) backBtn.addEventListener("click", () => {
    if(document.referrer && document.referrer.includes(location.host)) history.back();
    else location.href = "index.html";
  });
}

function socialIconLink(url, label, svg){
  if(!url || url === "#") return "";
  return `<a href="${esc(url)}" target="_blank" rel="noopener" aria-label="${label}">${svg}</a>`;
}

/* ---------- Footer (compact, 4 columns) ---------- */
function renderFooter(){
  const el = document.getElementById("siteFooter");
  if(!el) return;
  const addressLine = SITE.address || "";
  el.innerHTML = `
    <div class="container">
      <div class="footer-grid">
        <div class="footer-about">
          <a href="/" class="brand-link mb-2">
            <img src="${SITE.logo}" alt="${SITE.brand} logo" class="brand-logo">
            <span class="brand-name">${SITE.brand}</span>
          </a>
          <p>${esc(SITE.tagline) || "Premium handcrafted artificial flowers, torans, latkans, jhoomars &amp; malas — for weddings, festivals and everyday decor."}</p>
          <div class="footer-social">
            ${socialIconLink(SITE.facebook, "Facebook", '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M18 2h-3a5 5 0 00-5 5v3H7v4h3v8h4v-8h3l1-4h-4V7a1 1 0 011-1h3z"/></svg>')}
            ${socialIconLink(SITE.instagram, "Instagram", '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><rect x="3" y="3" width="18" height="18" rx="5"/><circle cx="12" cy="12" r="4"/><circle cx="17.5" cy="6.5" r="1"/></svg>')}
            ${socialIconLink(SITE.youtube, "YouTube", '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><rect x="2" y="5" width="20" height="14" rx="4"/><polygon points="10 9 15 12 10 15" fill="currentColor" stroke="none"/></svg>')}
            ${socialIconLink(SITE.twitter, "Twitter", '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M22 5.9c-.7.3-1.5.6-2.3.7a4 4 0 001.8-2.2c-.8.5-1.6.8-2.6 1a4 4 0 00-6.8 3.6A11.3 11.3 0 013 4.9a4 4 0 001.2 5.3 4 4 0 01-1.8-.5v.1a4 4 0 003.2 3.9 4 4 0 01-1.8.1 4 4 0 003.7 2.8A8 8 0 012 18.6a11.3 11.3 0 006.1 1.8c7.3 0 11.3-6 11.3-11.3v-.5c.8-.6 1.4-1.3 2-2.1z"/></svg>')}
            ${socialIconLink(SITE.pinterest, "Pinterest", '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><circle cx="12" cy="12" r="9"/><path d="M9 20c.6-2 1.2-4.3 2-7.5.4-1.7 3-1.7 3.5.2.4 1.5-.5 3.3-2.2 3.3-1 0-1.7-.5-2-1.2M11.7 8a2.3 2.3 0 014.5.6c0 1.9-1 3.8-1 3.8"/></svg>')}
            <a href="${waGeneralLink()}" target="_blank" rel="noopener" aria-label="WhatsApp">${ICONS.whatsapp}</a>
          </div>
        </div>

        <div class="footer-col">
          <h6>Quick Links</h6>
          <ul>
            <li><a href="/">Home</a></li>
            <li><a href="/categories">All Categories</a></li>
            <li><a href="/cart">Cart</a></li>
          </ul>
        </div>

        <div class="footer-col">
          <h6>Categories</h6>
          <ul>
            ${CATALOGUE.categories.map(c => `<li><a href="/categories?cat=${c.id}">${c.name}</a></li>`).join("")}
          </ul>
        </div>

        <div class="footer-col">
          <h6>Contact</h6>
          <ul>
            <li><a href="tel:${SITE.phone.replace(/\s/g,'')}">${SITE.phone}</a></li>
            <li><a href="mailto:${SITE.email}">${SITE.email}</a></li>
            <li><a href="${waGeneralLink()}" target="_blank" rel="noopener">Chat on WhatsApp</a></li>
            ${addressLine ? `<li class="footer-text-line">${esc(addressLine)}</li>` : ""}
            ${SITE.businessHours ? `<li class="footer-text-line">${esc(SITE.businessHours)}</li>` : ""}
          </ul>
        </div>
      </div>

      <div class="footer-bottom">
        <span>${SITE.footerCopyright ? esc(SITE.footerCopyright) : `© <span id="yr"></span> ${SITE.brand}. All Rights Reserved.`}</span>
      </div>
    </div>`;
  const yr = document.getElementById("yr");
  if(yr) yr.textContent = new Date().getFullYear();
}

/* ---------- Search overlay ---------- */
function allProductsFlat(){
  const out = [];
  Object.keys(CATALOGUE.products).forEach(subId => {
    CATALOGUE.products[subId].forEach(p => out.push(getProduct(subId, p.no)));
  });
  return out;
}

function initSearch(){
  const btn = document.getElementById("searchBtn");
  if(!btn) return;
  const overlay = document.createElement("div");
  overlay.className = "search-overlay";
  overlay.innerHTML = `
    <div class="search-panel">
      <div class="search-row">
        ${ICONS.search}
        <input type="text" id="searchInput" placeholder="Search products, SKU, category…" autocomplete="off">
        <button class="icon-btn" id="searchCloseBtn">${ICONS.close}</button>
      </div>
      <div class="search-results" id="searchResultsWrap"></div>
    </div>`;
  document.body.appendChild(overlay);
  const input = overlay.querySelector("#searchInput");
  const results = overlay.querySelector("#searchResultsWrap");

  function open(){ overlay.classList.add("open"); document.body.style.overflow = "hidden"; setTimeout(() => input.focus(), 150); }
  function close(){ overlay.classList.remove("open"); document.body.style.overflow = ""; }
  btn.addEventListener("click", open);
  overlay.querySelector("#searchCloseBtn").addEventListener("click", close);
  overlay.addEventListener("click", e => { if(e.target === overlay) close(); });
  document.addEventListener("keydown", e => { if(e.key === "Escape") close(); });

  const all = allProductsFlat();
  input.addEventListener("input", () => {
    const q = input.value.trim().toLowerCase();
    if(!q){ results.innerHTML = `<p class="search-hint">Start typing to search ${all.length}+ products…</p>`; return; }
    const matches = all.filter(p =>
      p.name.toLowerCase().includes(q) || (p.sku || "").toLowerCase().includes(q)
    ).slice(0, 20);
    if(!matches.length){ results.innerHTML = `<p class="search-hint">No products found for "${esc(q)}"</p>`; return; }
    results.innerHTML = matches.map(p => `
      <a class="search-result-item" href="/product.html?sub=${p.subId}&no=${p.no}">
        <img src="${p.imgSrc}" alt="${esc(p.name)}" loading="lazy">
        <div class="sri-meta">
          <div class="sri-name">${esc(p.name)}</div>
          <div class="sri-sub">${p.sku || ""}</div>
        </div>
        <div class="sri-price">${p.priceLabel}</div>
      </a>`).join("");
  });
  results.innerHTML = `<p class="search-hint">Start typing to search ${all.length}+ products…</p>`;
}

/* ---------- Toast ---------- */
function toast(msg){
  let t = document.getElementById("appToast");
  if(!t){ t = document.createElement("div"); t.id = "appToast"; t.className = "app-toast"; document.body.appendChild(t); }
  t.textContent = msg;
  t.classList.add("show");
  clearTimeout(t._timer);
  t._timer = setTimeout(() => t.classList.remove("show"), 2200);
}

document.addEventListener("DOMContentLoaded", () => {
  Promise.all([CATALOGUE_READY, SITE_READY]).then(() => {
  renderHeader();
  renderFooter();
  initSearch();
  });
});
