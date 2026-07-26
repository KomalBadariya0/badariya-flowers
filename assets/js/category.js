(function(){
  const params = new URLSearchParams(location.search);
  let catId = params.get("cat");
  let subId = params.get("sub");

  function findCat(id){ return CATALOGUE.categories.find(c => c.id === id); }

  // Auto-resolve: a category with exactly one subcategory behaves like that subcategory directly
  if(catId && !subId){
    const cat = findCat(catId);
    if(cat && cat.subcategories.length === 1) subId = cat.subcategories[0];
  }

  function setBreadcrumb(parts){
    // parts: [{label, href}] last one has no href (current)
    const html = parts.map((p, i) => {
      const isLast = i === parts.length - 1;
      const sep = i > 0 ? `<span class="sep">/</span>` : "";
      return sep + (isLast ? `<span class="current">${esc(p.label)}</span>` : `<a href="${p.href}">${esc(p.label)}</a>`);
    }).join(" ");
    document.getElementById("breadcrumbRow").innerHTML = `<a href="/">Home</a> ` + html;
  }

  function downloadBtn(href, label){
    return `<a class="btn-outline-dark" href="${href}" download>${ICONS.pdf} ${label || "Download PDF"}</a>`;
  }

  function renderSubcategoryProducts(subId){
    const meta = CATALOGUE.subcategories[subId];
    const cat = findCat(meta.parent);
    const products = (CATALOGUE.products[subId] || []).map(p => getProduct(subId, p.no));

    document.getElementById("pageTitleTag").textContent = `${meta.name} — ${SITE.brand}`;
    setBreadcrumb([
      { label: cat.name, href: `category.html?cat=${cat.id}` },
      { label: meta.name }
    ]);
    document.getElementById("pageTitle").textContent = meta.name;
    document.getElementById("pageCount").textContent = `${products.length} items`;

    const pdfHref = CATALOGUE.pdfs[subId];
    document.getElementById("pageActions").innerHTML = pdfHref ? downloadBtn(pdfHref) : "";

    document.getElementById("productGridWrap").style.display = "block";
    document.getElementById("productGrid").innerHTML = products.map(productCardHTML).join("");
    wireCartButtons(document);
  }

  function renderCategoryPicker(catId){
    const cat = findCat(catId);
    if(!cat){ renderAllCategories(); return; }
    const totalCount = cat.subcategories.reduce((n, s) => n + (CATALOGUE.products[s]?.length || 0), 0);

    document.getElementById("pageTitleTag").textContent = `${cat.name} — ${SITE.brand}`;
    setBreadcrumb([{ label: cat.name }]);
    document.getElementById("pageTitle").textContent = cat.name;
    document.getElementById("pageCount").textContent = `${totalCount} items`;
    document.getElementById("pageActions").innerHTML = downloadBtn(CATALOGUE.fullCatalogue, "Download Full Catalogue");

    const grid = document.getElementById("subcatGrid");
    grid.style.display = "grid";
    grid.innerHTML = cat.subcategories.map(sId => {
      const meta = CATALOGUE.subcategories[sId];
      const count = (CATALOGUE.products[sId] || []).length;
      return subcatCardHTML(sId, meta, count);
    }).join("");
  }

  function renderAllCategories(){
    document.getElementById("pageTitleTag").textContent = `All Categories — ${SITE.brand}`;
    setBreadcrumb([{ label: "All Categories" }]);
    document.getElementById("pageTitle").textContent = "All Categories";
    const total = Object.values(CATALOGUE.products).reduce((n, l) => n + l.length, 0);
    document.getElementById("pageCount").textContent = `${total} items`;
    document.getElementById("pageActions").innerHTML = downloadBtn(CATALOGUE.fullCatalogue, "Download Full Catalogue");

    const grid = document.getElementById("allCatGrid");
    grid.style.display = "grid";
    grid.innerHTML = CATALOGUE.categories.map(c => {
      const count = c.subcategories.reduce((n, s) => n + (CATALOGUE.products[s]?.length || 0), 0);
      return categoryCardHTML(c, count);
    }).join("");
  }

  function init(){
    document.getElementById("fabWa").innerHTML = ICONS.whatsapp;
    document.getElementById("fabWa").href = waGeneralLink();

    if(subId && CATALOGUE.subcategories[subId]){
      renderSubcategoryProducts(subId);
    } else if(catId && findCat(catId)){
      renderCategoryPicker(catId);
    } else {
      renderAllCategories();
    }
    initReveal();
  }

  document.addEventListener("DOMContentLoaded", () => { Promise.all([CATALOGUE_READY, SITE_READY]).then(init); });
})();
