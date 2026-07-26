/* ==========================================================================
   SEARCH.JS — live search across the full catalogue
   ========================================================================== */

(function(){
  const panel = document.getElementById("searchPanel");
  const input = document.getElementById("searchInput");
  const results = document.getElementById("searchResults");
  const openBtns = document.querySelectorAll("[data-open-search]");
  const closeBtn = document.getElementById("searchClose");

  let flatIndex = null;
  function buildIndex(){
    if(flatIndex) return flatIndex;
    flatIndex = [];
    Object.keys(CATALOGUE.products).forEach(subId => {
      CATALOGUE.products[subId].forEach(p => {
        flatIndex.push(getProduct(subId, p.no));
      });
    });
    return flatIndex;
  }

  function open(){
    panel.classList.add("is-open");
    buildIndex();
    setTimeout(() => input.focus(), 150);
    document.body.style.overflow = "hidden";
  }
  function close(){
    panel.classList.remove("is-open");
    document.body.style.overflow = "";
  }

  openBtns.forEach(b => b.addEventListener("click", (e) => { e.preventDefault(); open(); }));
  closeBtn.addEventListener("click", close);
  panel.addEventListener("click", (e) => { if(e.target === panel) close(); });
  document.addEventListener("keydown", (e) => { if(e.key === "Escape") close(); });

  function render(list){
    if(!list.length){
      results.innerHTML = `<p class="search-empty">No products found. Try “toran”, “latkan”, or “jhoomar”.</p>`;
      return;
    }
    results.innerHTML = list.slice(0, 24).map(p => `
      <a class="search-result" href="/product.html?sub=${p.subId}&no=${p.no}">
        <img src="${p.imgSrc}" alt="${p.name}" loading="lazy">
        <span>
          <span class="sr-name">${p.name}${p.sku ? " — " + p.sku : ""}</span><br>
          <span class="sr-meta">${CATALOGUE.subcategories[p.subId]?.name || ""} · ${p.priceLabel}</span>
        </span>
      </a>
    `).join("");
  }

  input.addEventListener("input", () => {
    const q = input.value.trim().toLowerCase();
    const idx = buildIndex();
    if(!q){ results.innerHTML = ""; return; }
    const matches = idx.filter(p =>
      p.name.toLowerCase().includes(q) ||
      (p.sku || "").toLowerCase().includes(q) ||
      (CATALOGUE.subcategories[p.subId]?.name || "").toLowerCase().includes(q)
    );
    render(matches);
  });
})();
