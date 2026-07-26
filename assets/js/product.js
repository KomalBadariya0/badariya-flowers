(function(){
  const params = new URLSearchParams(location.search);
  const subId = params.get("sub");
  const no = parseInt(params.get("no"), 10);

  function relatedCardHTML(p){ return productCardHTML(p); }

  function render(){
    document.getElementById("fabWa").innerHTML = ICONS.whatsapp;
    document.getElementById("fabWa").href = waGeneralLink();

    const p = subId ? getProduct(subId, no) : null;
    if(!p){
      document.querySelector("main").style.display = "none";
      document.getElementById("notFoundWrap").style.display = "block";
      return;
    }

    const meta = CATALOGUE.subcategories[subId];
    const cat = CATALOGUE.categories.find(c => c.id === meta.parent);

    document.getElementById("pageTitleTag").textContent = `${p.name} — ${SITE.brand}`;

    document.getElementById("breadcrumbRow").innerHTML = `
      <a href="/">Home</a> <span class="sep">/</span>
      <a href="/categories?cat=${cat.id}">${esc(cat.name)}</a> <span class="sep">/</span>
      <a href="/categories?cat=${cat.id}&sub=${subId}">${esc(meta.name)}</a> <span class="sep">/</span>
      <span class="current">${esc(p.name)}</span>`;

    document.getElementById("pdpImg").src = p.imgSrc;
    document.getElementById("pdpImg").alt = p.name;

    document.getElementById("pdpCatTag").textContent = meta.name;
    document.getElementById("pdpTitle").textContent = p.name;
    document.getElementById("pdpSku").textContent = p.sku ? `SKU: ${p.sku}` : "";
    document.getElementById("pdpPrice").textContent = p.priceLabel;
    document.getElementById("pdpMoq").textContent = `MOQ: ${p.moq}`;

    if(p.desc){
      document.getElementById("pdpDesc").textContent = p.desc;
    } else {
      document.getElementById("pdpDescWrap").style.display = "none";
    }

    /* Prev / Next navigation within the same subcategory */
    const siblingList = CATALOGUE.products[subId] || [];
    const idx = siblingList.findIndex(x => x.no === no);
    const prevItem = idx > 0 ? siblingList[idx - 1] : siblingList[siblingList.length - 1];
    const nextItem = idx < siblingList.length - 1 ? siblingList[idx + 1] : siblingList[0];
    const prevBtn = document.getElementById("pdpPrevBtn");
    const nextBtn = document.getElementById("pdpNextBtn");
    prevBtn.innerHTML = ICONS.chevronLeft;
    nextBtn.innerHTML = ICONS.arrow;
    if(siblingList.length > 1){
      prevBtn.addEventListener("click", () => location.href = `product.html?sub=${subId}&no=${prevItem.no}`);
      nextBtn.addEventListener("click", () => location.href = `product.html?sub=${subId}&no=${nextItem.no}`);
    } else {
      prevBtn.style.display = "none";
      nextBtn.style.display = "none";
    }

    const addBtn = document.getElementById("pdpAddCartBtn");
    addBtn.addEventListener("click", () => {
      cartAdd(subId, no);
      addBtn.textContent = "Added ✓";
      toast(`Added to cart (MOQ ${p.moq})`);
      setTimeout(() => { addBtn.textContent = "Add to Cart"; }, 1600);
    });

    /* Related products: rest of the same subcategory */
    const related = (CATALOGUE.products[subId] || [])
      .filter(x => x.no !== no)
      .map(x => getProduct(subId, x.no))
      .slice(0, 10);
    document.getElementById("relatedScroller").innerHTML = related.map(relatedCardHTML).join("");
    wireCartButtons(document);

    initReveal();
  }

  document.addEventListener("DOMContentLoaded", () => { Promise.all([CATALOGUE_READY, SITE_READY]).then(render); });
})();
