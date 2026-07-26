/* ==========================================================================
   CARD TEMPLATES — category card, product card (reference-matched structure)
   ========================================================================== */

function categoryCardHTML(cat, count){
  return `
    <a href="/categories?cat=${cat.id}" class="cat-card reveal">
      <div class="cat-card-media"><img src="${cat.cover}" alt="${esc(cat.name)}" loading="lazy"></div>
      <div class="cat-card-body">
        <div class="name">${esc(cat.name)}</div>
        <div class="count">${count} items</div>
      </div>
    </a>`;
}

function subcatCardHTML(subId, subMeta, count){
  const firstProduct = (CATALOGUE.products[subId] || [])[0];
  const cover = subMeta.cover || (firstProduct ? `assets/images/products/${subId}/${firstProduct.img}.png` : "");
  return `
    <a href="/categories?cat=${subMeta.parent}&sub=${subId}" class="cat-card reveal">
      <div class="cat-card-media"><img src="${cover}" alt="${esc(subMeta.name)}" loading="lazy"></div>
      <div class="cat-card-body">
        <div class="name">${esc(subMeta.name)}</div>
        <div class="count">${count} items</div>
      </div>
    </a>`;
}

function productCardHTML(p){
  const key = `${p.subId}:${p.no}`;
  return `
    <div class="product-card reveal" data-key="${key}">
      <a href="/product.html?sub=${p.subId}&no=${p.no}" class="pc-media">
        <img src="${p.imgSrc}" alt="${esc(p.name)}" loading="lazy">
      </a>
      <div class="pc-body">
        <a href="/product.html?sub=${p.subId}&no=${p.no}">
          <div class="pc-name">${esc(p.name)}</div>
        </a>
        ${p.sku ? `<div class="pc-sku">SKU: ${esc(p.sku)}</div>` : ""}
        <div class="pc-price ${p.price == null ? 'small' : ''}">${p.priceLabel}</div>
      </div>
      <button class="pc-cart-btn" data-add-cart data-sub="${p.subId}" data-no="${p.no}">Add to Cart</button>
    </div>`;
}

function wireCartButtons(root){
  (root || document).querySelectorAll("[data-add-cart]").forEach(btn => {
    btn.addEventListener("click", (e) => {
      e.preventDefault();
      const subId = btn.getAttribute("data-sub");
      const no = parseInt(btn.getAttribute("data-no"), 10);
      cartAdd(subId, no);
      btn.textContent = "Added ✓";
      btn.classList.add("added");
      toast("Added to cart");
      setTimeout(() => { btn.textContent = "Add to Cart"; btn.classList.remove("added"); }, 1400);
    });
  });
}

function initReveal(){
  const els = document.querySelectorAll(".reveal");
  if(!("IntersectionObserver" in window)){ els.forEach(e => e.classList.add("in")); return; }
  const io = new IntersectionObserver(entries => {
    entries.forEach(en => { if(en.isIntersecting){ en.target.classList.add("in"); io.unobserve(en.target); } });
  }, { threshold:0.1 });
  els.forEach(e => io.observe(e));
}
