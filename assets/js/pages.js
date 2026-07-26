/* ==========================================================================
   PAGES.JS — category, product-details & download-catalogue page rendering
   Driven entirely by CATALOGUE (assets/js/catalog.js) + the URL query string.
   ========================================================================== */

function qParam(name){
  return new URLSearchParams(window.location.search).get(name);
}

/* ---------------- CATEGORY PAGE ---------------- */
function initCategoryPage(){
  const grid = document.getElementById("categoryGrid");
  if(!grid) return;

  const PAGE_SIZE = 9;
  let currentPage = 1;
  let activeCat = qParam("cat") || CATALOGUE.categories[0].id;
  let activeSub = qParam("sub") || "all";
  let searchQuery = "";
  let sortMode = "latest";

  function currentCat(){
    return CATALOGUE.categories.find(c => c.id === activeCat) || CATALOGUE.categories[0];
  }

  function productsForView(){
    if(activeCat === "all"){
      return Object.keys(CATALOGUE.products).flatMap(subId =>
        CATALOGUE.products[subId].map(p => getProduct(subId, p.no))
      );
    }
    const cat = currentCat();
    if(activeSub !== "all") return (CATALOGUE.products[activeSub] || []).map(p => getProduct(activeSub, p.no));
    return getCategoryProducts(cat.id);
  }

  function applyFilters(){
    let list = productsForView();
    if(searchQuery){
      const q = searchQuery;
      list = list.filter(p =>
        p.name.toLowerCase().includes(q) ||
        (p.sku || "").toLowerCase().includes(q) ||
        (CATALOGUE.subcategories[p.subId]?.name || "").toLowerCase().includes(q)
      );
    }
    list = list.slice();
    if(sortMode === "price-low") list.sort((a,b) => (a.price ?? 999999) - (b.price ?? 999999));
    else if(sortMode === "price-high") list.sort((a,b) => (b.price ?? -1) - (a.price ?? -1));
    else if(sortMode === "name") list.sort((a,b) => a.name.localeCompare(b.name));
    return list;
  }

  function updateHeader(){
    const cat = activeCat === "all" ? { name:"All Categories" } : currentCat();
    let title = cat.name;
    if(activeSub !== "all") title = CATALOGUE.subcategories[activeSub]?.name || title;
    document.title = `${title} — Badariya Flowers`;
    const crumbCurrent = document.getElementById("crumbCurrent");
    if(crumbCurrent) crumbCurrent.textContent = title;
    document.getElementById("catTitle").textContent = title;

    const downloadBtn = document.getElementById("catDownloadBtn");
    if(downloadBtn){
      const pdf = activeSub !== "all" ? CATALOGUE.pdfs[activeSub] : (activeCat !== "all" ? CATALOGUE.pdfs[currentCat().subcategories[0]] : CATALOGUE.fullCatalogue);
      downloadBtn.href = pdf || CATALOGUE.fullCatalogue;
      downloadBtn.setAttribute("download", "");
    }
  }

  function renderSidebar(){
    const wrap = document.getElementById("sidebarCatList");
    if(!wrap) return;
    let html = `<div class="sidebar-cat"><button class="sidebar-cat-btn ${activeCat==='all'?'is-active':''}" data-cat="all">All Categories</button></div>`;
    CATALOGUE.categories.forEach(cat => {
      const isActiveCat = cat.id === activeCat;
      const hasSubs = cat.subcategories && cat.subcategories.length > 1;
      html += `<div class="sidebar-cat ${isActiveCat && hasSubs ? 'is-open':''}">
        <button class="sidebar-cat-btn ${isActiveCat?'is-active':''}" data-cat="${cat.id}">
          <span>${cat.name}</span>
          ${hasSubs ? `<svg class="chev" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M9 6l6 6-6 6"/></svg>` : ""}
        </button>
        ${hasSubs ? `<div class="sidebar-sub-list">
          ${cat.subcategories.map(subId => `<button class="sidebar-sub-btn ${isActiveCat && activeSub===subId ? 'is-active':''}" data-cat="${cat.id}" data-sub="${subId}">${CATALOGUE.subcategories[subId]?.name || subId}</button>`).join("")}
        </div>` : ""}
      </div>`;
    });
    wrap.innerHTML = html;

    wrap.querySelectorAll(".sidebar-cat-btn").forEach(btn => {
      btn.addEventListener("click", () => {
        activeCat = btn.dataset.cat;
        activeSub = "all";
        currentPage = 1;
        goToState();
      });
    });
    wrap.querySelectorAll(".sidebar-sub-btn").forEach(btn => {
      btn.addEventListener("click", (e) => {
        e.stopPropagation();
        activeCat = btn.dataset.cat;
        activeSub = btn.dataset.sub;
        currentPage = 1;
        goToState();
      });
    });
  }

  function goToState(){
    const params = new URLSearchParams();
    if(activeCat !== "all") params.set("cat", activeCat);
    if(activeSub !== "all") params.set("sub", activeSub);
    const qs = params.toString();
    history.pushState(null, "", qs ? `/categories?${qs}` : "/categories");
    renderSidebar();
    updateHeader();
    renderGrid();
  }

  function renderGrid(){
    const filtered = applyFilters();
    const start = (currentPage - 1) * PAGE_SIZE;
    const pageItems = filtered.slice(start, start + PAGE_SIZE);
    grid.innerHTML = pageItems.map(productCard).join("") ||
      `<p class="search-empty" style="grid-column:1/-1;">No products match your search. Try a different term.</p>`;
    document.getElementById("catCount").textContent = filtered.length;
    renderPagination(filtered.length);
    initReveal();
  }

  function renderPagination(total){
    const wrap = document.getElementById("categoryPagination");
    const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));
    if(totalPages <= 1){ wrap.innerHTML = ""; return; }

    const pagesToShow = new Set([1, 2, totalPages, totalPages - 1, currentPage - 1, currentPage, currentPage + 1]);
    let html = `<button class="page-btn ${currentPage===1?'is-disabled':''}" data-page="${currentPage-1}" aria-label="Previous page">‹</button>`;
    let lastShown = 0;
    for(let i=1;i<=totalPages;i++){
      if(i < 1 || i > totalPages) continue;
      if(!pagesToShow.has(i)) continue;
      if(i - lastShown > 1) html += `<span class="page-btn is-disabled" style="border:none;background:none;">…</span>`;
      html += `<button class="page-btn ${i===currentPage?'is-active':''}" data-page="${i}">${i}</button>`;
      lastShown = i;
    }
    html += `<button class="page-btn ${currentPage===totalPages?'is-disabled':''}" data-page="${currentPage+1}" aria-label="Next page">›</button>`;
    wrap.innerHTML = html;
    wrap.querySelectorAll(".page-btn[data-page]").forEach(btn => {
      btn.addEventListener("click", () => {
        const p = parseInt(btn.dataset.page, 10);
        if(p >= 1 && p <= totalPages){
          currentPage = p;
          renderGrid();
          document.querySelector(".category-page-header")?.scrollIntoView({ behavior:"smooth", block:"start" });
        }
      });
    });
  }

  const searchInput = document.getElementById("categorySearchInput");
  if(searchInput){
    searchInput.addEventListener("input", () => {
      searchQuery = searchInput.value.trim().toLowerCase();
      currentPage = 1;
      renderGrid();
    });
  }
  const sortSelect = document.getElementById("sortSelect");
  if(sortSelect){
    sortSelect.addEventListener("change", () => {
      sortMode = sortSelect.value;
      currentPage = 1;
      renderGrid();
    });
  }
  const shareBtn = document.getElementById("catShareBtn");
  if(shareBtn){
    shareBtn.addEventListener("click", () => sharePage(currentCat().name || "Category"));
  }

  renderSidebar();
  updateHeader();
  renderGrid();

  window.addEventListener("popstate", () => {
    activeCat = qParam("cat") || "all";
    activeSub = qParam("sub") || "all";
    currentPage = 1;
    renderSidebar();
    updateHeader();
    renderGrid();
  });
}

/* Web Share API with clipboard fallback, used by category & product pages */
function sharePage(title){
  const url = window.location.href;
  if(navigator.share){
    navigator.share({ title: `${title} — Badariya Flowers`, url }).catch(() => {});
  } else if(navigator.clipboard){
    navigator.clipboard.writeText(url).then(() => alert("Link copied to clipboard!"));
  } else {
    prompt("Copy this link:", url);
  }
}

/* ---------------- PRODUCT DETAILS PAGE ---------------- */
function initProductPage(){
  const infoEl = document.getElementById("productInfo");
  if(!infoEl) return;

  const subId = qParam("sub");
  const no = parseInt(qParam("no"), 10);
  const p = getProduct(subId, no);

  if(!p){
    infoEl.innerHTML = `
      <span class="eyebrow">Not Found</span>
      <h1>We couldn't find that design</h1>
      <p class="product-short-desc">It may have moved or the link is outdated. Browse the full collection instead.</p>
      <div class="product-actions">
        <a href="/" class="btn btn-primary">Back to Home</a>
        <a href="/categories?cat=toran" class="btn btn-outline">Browse Collection</a>
      </div>`;
    const galleryMain = document.querySelector(".product-gallery");
    if(galleryMain) galleryMain.style.display = "none";
    return;
  }

  const sub = CATALOGUE.subcategories[subId];
  const cat = CATALOGUE.categories.find(c => c.id === sub?.parent);

  document.title = `${p.name} — Badariya Flowers`;

  const crumbCat = document.getElementById("crumbCat");
  if(crumbCat && cat){ crumbCat.textContent = cat.name; crumbCat.href = `category.html?cat=${cat.id}`; }
  const crumbCurrent = document.getElementById("crumbCurrent");
  if(crumbCurrent) crumbCurrent.textContent = p.name;

  /* ---- Gallery: single authentic photo today; structured for multi-image later ---- */
  const images = [p.imgSrc];
  let activeImg = 0;
  const img = document.getElementById("productGalleryImg");
  const badge = document.getElementById("galleryBadge");
  if(badge) badge.textContent = sub ? sub.name : "";

  function renderGallery(){
    img.src = images[activeImg];
    img.alt = `${p.name} - ${p.sku || ""}`;
    const thumbs = document.getElementById("galleryThumbs");
    if(thumbs){
      thumbs.innerHTML = images.map((src, i) =>
        `<button class="product-gallery-thumb ${i===activeImg?'is-active':''}" data-i="${i}"><img src="${src}" alt="${p.name} thumbnail ${i+1}"></button>`
      ).join("");
      thumbs.querySelectorAll(".product-gallery-thumb").forEach(btn => {
        btn.addEventListener("click", () => { activeImg = parseInt(btn.dataset.i, 10); renderGallery(); });
      });
    }
  }
  renderGallery();
  const prevBtn = document.getElementById("galleryPrev");
  const nextBtn = document.getElementById("galleryNext");
  if(prevBtn) prevBtn.addEventListener("click", () => { activeImg = (activeImg - 1 + images.length) % images.length; renderGallery(); });
  if(nextBtn) nextBtn.addEventListener("click", () => { activeImg = (activeImg + 1) % images.length; renderGallery(); });
  if(images.length <= 1){ if(prevBtn) prevBtn.style.display = "none"; if(nextBtn) nextBtn.style.display = "none"; }

  /* ---- Info panel ---- */
  infoEl.innerHTML = `
    <span class="eyebrow">${cat ? cat.name : ""}</span>
    <h1>${p.name}</h1>
    <div class="product-info-top">
      ${p.sku ? `<span class="product-info-sku">SKU: ${p.sku}</span>` : ""}
      <span class="badge-instock">In Stock</span>
    </div>
    <p class="product-short-desc">${p.desc || `High quality ${p.name.toLowerCase()} for decoration and all occasion use.`}</p>
    <div class="product-price-row">
      <span class="price ${p.price == null ? 'small' : ''}">${p.priceLabel}</span>
    </div>
    <ul class="product-features">
      <li><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="9"/><path d="M9 12l2 2 4-4"/></svg>Premium Quality</li>
      <li><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="9"/><path d="M9 12l2 2 4-4"/></svg>Beautiful Handcrafted Design</li>
      <li><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="9"/><path d="M9 12l2 2 4-4"/></svg>Durable &amp; Long Lasting</li>
      <li><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="9"/><path d="M9 12l2 2 4-4"/></svg>Perfect for Decoration</li>
      ${p.size ? `<li><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="9"/><path d="M9 12l2 2 4-4"/></svg>Size: ${p.size}</li>` : ""}
    </ul>
    <div class="product-actions">
      <a class="btn btn-primary btn-block" href="${waLink(productWaMessage(p))}" target="_blank" rel="noopener">
        <svg viewBox="0 0 24 24" fill="currentColor" style="width:16px;height:16px;"><path d="M17.5 14.4c-.3-.1-1.7-.9-2-1-.3-.1-.5-.1-.7.1-.2.3-.8 1-.9 1.1-.2.2-.3.2-.6.1-.3-.1-1.2-.4-2.3-1.4-.9-.8-1.4-1.7-1.6-2-.2-.3 0-.5.1-.6.1-.1.3-.3.4-.5.1-.1.2-.3.3-.5.1-.2 0-.4 0-.5C10.1 9 9.6 7.7 9.4 7.2c-.2-.5-.4-.4-.6-.4h-.5c-.2 0-.5.1-.7.3-.2.3-.9.9-.9 2.2s1 2.6 1.1 2.7c.1.2 2 3 4.8 4.2.7.3 1.2.5 1.6.6.7.2 1.3.2 1.8.1.6-.1 1.7-.7 1.9-1.3.2-.7.2-1.2.2-1.3-.1-.1-.3-.2-.6-.3z"/><path d="M12 2C6.5 2 2 6.5 2 12c0 1.9.5 3.7 1.5 5.3L2 22l4.8-1.5c1.5.9 3.3 1.3 5.2 1.3 5.5 0 10-4.5 10-10S17.5 2 12 2zm0 18.1c-1.7 0-3.3-.5-4.7-1.3l-.3-.2-3.2 1 1-3.1-.2-.3C3.6 15 3 13.5 3 12c0-5 4-9 9-9s9 4 9 9-4 9-9 9z"/></svg>
        Enquire on WhatsApp
      </a>
      <button class="btn btn-outline btn-block" id="shareProductBtn" type="button">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:15px;height:15px;"><circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/><path d="M8.6 13.5l6.8 4M15.4 6.5l-6.8 4"/></svg>
        Share Product
      </button>
    </div>
    <div class="qr-box">
      <img src="https://api.qrserver.com/v1/create-qr-code/?size=160x160&color=58-44-35&bgcolor=255-252-248&data=${encodeURIComponent(waLink(productWaMessage(p)))}" alt="QR code to enquire about ${p.name} on WhatsApp" loading="lazy">
      <div>
        <h5>Scan to Enquire</h5>
        <p>Scan this QR code on WhatsApp to enquire about this product</p>
      </div>
    </div>
  `;

  const shareBtn = document.getElementById("shareProductBtn");
  if(shareBtn) shareBtn.addEventListener("click", () => sharePage(p.name));

  /* ---- Lower grid: description + download ---- */
  const lowerGrid = document.getElementById("productLowerGrid");
  if(lowerGrid){
    const pdf = CATALOGUE.pdfs[subId];
    lowerGrid.innerHTML = `
      <div class="product-desc-block" data-reveal>
        <h4>Product Description</h4>
        <p>${p.desc || `This is a high quality ${p.name.toLowerCase()} used for decoration, wedding stage, backdrop, mandap and all types of events. Made with the best quality materials for long lasting use and a beautiful look.`}</p>
        <div class="product-tags">
          <span><strong>Categories:</strong> ${cat ? cat.name : "—"}${sub ? " › " + sub.name : ""}</span>
          <span><strong>Tag:</strong> ${p.name}</span>
        </div>
      </div>
      <div class="download-box" data-reveal>
        <h4>Download Catalog</h4>
        <p>Download this category catalog in PDF format.</p>
        ${pdf
          ? `<a class="btn btn-primary btn-sm btn-icon-sm btn-block" href="${pdf}" download><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:15px;height:15px;"><path d="M12 3v12m0 0l-4-4m4 4l4-4"/><path d="M4 19h16"/></svg>Download PDF</a>`
          : `<a class="btn btn-outline btn-sm btn-block" href="#" data-wa-general>Ask on WhatsApp</a>`}
      </div>
    `;
    if(!pdf){
      const waBtn = lowerGrid.querySelector("[data-wa-general]");
      if(waBtn){ waBtn.href = waLink("Hi Badariya Flowers! I'd like to know more about your collection."); waBtn.target = "_blank"; waBtn.rel = "noopener"; }
    }
  }

  const relatedWrap = document.getElementById("relatedGrid");
  if(relatedWrap){
    const related = (CATALOGUE.products[subId] || [])
      .filter(x => x.no !== no)
      .slice(0, 8)
      .map(x => getProduct(subId, x.no));
    relatedWrap.innerHTML = related.map(productCard).join("");
  }

  initReveal();
}

/* ---------------- DOWNLOAD CATALOGUE PAGE ---------------- */
function initCataloguePage(){
  const wrap = document.getElementById("catalogueSections");
  if(!wrap) return;

  wrap.innerHTML = CATALOGUE.categories.map(cat => {
    const cards = cat.subcategories.map(subId => {
      const sub = CATALOGUE.subcategories[subId];
      const list = CATALOGUE.products[subId] || [];
      const count = list.length;
      const pdf = CATALOGUE.pdfs[subId];
      const cover = sub.cover || (list[0] ? `assets/images/products/${subId}/${list[0].img}.png` : cat.cover);
      return `
      <div class="catalogue-card" data-reveal>
        <div class="catalogue-card-media"><img src="${cover}" alt="${sub.name}" loading="lazy"></div>
        <div class="catalogue-card-body">
          <h3>${sub.name}</h3>
          <p>${count} designs from the official Badariya Flowers catalogue.</p>
          ${pdf
            ? `<a class="btn btn-primary btn-sm btn-block" href="${pdf}" download>Download PDF</a>`
            : `<a class="btn btn-outline btn-sm btn-block" href="#" data-wa-general>Ask on WhatsApp</a>`}
        </div>
      </div>`;
    }).join("");
    return `
    <h3 class="catalogue-section-title" id="cat-${cat.id}" data-reveal>${cat.name}</h3>
    <div class="catalogue-grid">${cards}</div>`;
  }).join("");

  document.querySelectorAll("#catalogueSections [data-wa-general]").forEach(btn => {
    btn.href = waLink("Hi Badariya Flowers! I'd like to know more about your genda toran, jhoomar & latkan collection.");
    btn.target = "_blank"; btn.rel = "noopener";
  });

  initReveal();
}

document.addEventListener("DOMContentLoaded", () => {
  CATALOGUE_READY.then(() => {
  try { initCategoryPage(); } catch(err) { console.error("initCategoryPage failed:", err); }
  try { initProductPage(); } catch(err) { console.error("initProductPage failed:", err); }
  try { initCataloguePage(); } catch(err) { console.error("initCataloguePage failed:", err); }
  });
});
