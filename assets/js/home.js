(function(){
  function render(){
    /* ---- icons ---- */
    document.getElementById("fabWa").innerHTML = ICONS.whatsapp;
    document.getElementById("fabWa").href = waGeneralLink();
    document.getElementById("icArrow1").innerHTML = ICONS.arrow;
    const totalProducts = Object.values(CATALOGUE.products).reduce((n,l) => n + l.length, 0);
    const heroCount = document.getElementById("heroDesignCount");
    if(heroCount) heroCount.textContent = `${totalProducts}+`;
    document.getElementById("icQuality").innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M12 2l2.9 6.3L21 9l-4.9 4.4L17.5 21 12 17.6 6.5 21l1.4-7.6L3 9l6.1-.7z"/></svg>';
    document.getElementById("icPrice").innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M12 1v22M17 5H9.5a3.5 3.5 0 000 7h5a3.5 3.5 0 010 7H6"/></svg>';
    document.getElementById("icFast").innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M13 2 3 14h8l-1 8 10-12h-8z"/></svg>';
    document.getElementById("icDelivery").innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><rect x="1" y="3" width="15" height="13"/><polygon points="16 8 20 8 23 11 23 16 16 16 16 8"/><circle cx="5.5" cy="18.5" r="2.5"/><circle cx="18.5" cy="18.5" r="2.5"/></svg>';

    /* ---- category scroller ---- */
    const catWrap = document.getElementById("categoryScroller");
    catWrap.innerHTML = CATALOGUE.categories.map(c => {
      const count = c.subcategories.reduce((n, s) => n + (CATALOGUE.products[s]?.length || 0), 0);
      return categoryCardHTML(c, count);
    }).join("");

    /* ---- featured products ---- */
    const featuredSection = document.getElementById("featuredSection");
    const featuredList = CATALOGUE.featured
      .map(([subId, no]) => getProduct(subId, no))
      .filter(Boolean);
    if(featuredList.length){
      document.getElementById("featuredScroller").innerHTML = featuredList.map(productCardHTML).join("");
      featuredSection.style.display = "";
    }

    /* ---- per-category subcategory sections (e.g. "Toran's" -> 6/4/3/10 Feet Toran cards) ---- */
    const catSectionsWrap = document.getElementById("categorySections");
    let sectionsHtml = "";
    CATALOGUE.categories.forEach(cat => {
      const cardsHtml = cat.subcategories.map(subId => {
        const meta = CATALOGUE.subcategories[subId];
        const count = (CATALOGUE.products[subId] || []).length;
        return subcatCardHTML(subId, meta, count);
      }).join("");
      sectionsHtml += `
        <section class="section">
          <div class="container">
            <div class="section-head reveal">
              <h2>${esc(cat.name)}</h2>
              <a href="/categories?cat=${cat.id}" class="view-all">View All <span class="ic-arrow"></span></a>
            </div>
            <div class="cat-scroll">${cardsHtml}</div>
          </div>
        </section>`;
    });
    catSectionsWrap.innerHTML = sectionsHtml;
    document.querySelectorAll(".ic-arrow").forEach(el => el.innerHTML = ICONS.arrow);

    wireCartButtons(document);
    initReveal();
  }
  document.addEventListener("DOMContentLoaded", () => { Promise.all([CATALOGUE_READY, SITE_READY]).then(render); });
})();
