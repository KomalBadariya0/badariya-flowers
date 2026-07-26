/* ==========================================================================
   BADARIYA FLOWERS — LIVE CATALOGUE (FastAPI-backed)
   ----------------------------------------------------------------------
   CATALOGUE used to be a hardcoded object. It is now populated at runtime
   from the FastAPI backend (see assets/js/api.js for API_BASE / Api).

   Every other site script (main.js, home.js, category.js, product.js,
   pages.js, search.js, cards.js) reads the global `CATALOGUE` object the
   exact same way it always did — shape is unchanged:
     CATALOGUE.categories    -> [{ id, name, tagline, cover, subcategories:[] }]
     CATALOGUE.subcategories -> { [subId]: { name, parent } }
     CATALOGUE.products      -> { [subId]: [ {no,name,sku,price,...} ] }
     CATALOGUE.featured / .newArrivals -> [ [subId, no], ... ]
     CATALOGUE.pdfs / .fullCatalogue   -> PDF URLs

   `id` for a category/sub-category is its SLUG (not the numeric DB id) —
   this keeps every existing URL (category.html?cat=toran,
   product.html?sub=toran-3ft&no=5) and every helper below working with
   zero changes anywhere else in the codebase.

   Categories are live from /api/categories, and Sub Categories are live
   from /api/subcategories (matched to their parent category via
   categoryId -> category slug). Products / catalogue PDFs are still
   wired in a later phase — until then they're empty so pages render
   cleanly with 0 items instead of crashing.

   Every page that uses CATALOGUE must wait on CATALOGUE_READY (a Promise)
   before rendering — see main.js/home.js/category.js/product.js/pages.js's
   DOMContentLoaded handlers, each wrapped as:
     document.addEventListener("DOMContentLoaded", () => { CATALOGUE_READY.then(render); });
   ========================================================================== */

const CATALOGUE = {
  categories: [],
  subcategories: {},
  products: {},
  featured: [],
  newArrivals: [],
  pdfs: {},
  fullCatalogue: ""
};

const CATALOGUE_READY = (async function loadCatalogue(){
  // categoryId (numeric, DB primary key) -> category slug. Sub categories
  // are only linked to their parent by numeric categoryId, but every page
  // on the site addresses categories by SLUG (category.html?cat=toran), so
  // this map is what lets us translate one into the other below.
  const idToSlug = {};

  try{
    const catRes = await Api.get("/categories", { status: "active" });
    CATALOGUE.categories = (catRes.data || []).map(c => {
      idToSlug[c.id] = c.slug;
      return {
        id: c.slug,
        name: c.name,
        tagline: c.tagline || "",
        cover: mediaUrl(c.image) || "",
        subcategories: [] // filled in below from /api/subcategories
      };
    });
  }catch(err){
    console.error("Could not load categories from the backend:", err.message);
    CATALOGUE.categories = [];
  }

  try{
    const subRes = await Api.get("/subcategories", { status: "active" });
    const subIdToSlug = {};
    (subRes.data || []).forEach(s => {
      const parentSlug = idToSlug[s.categoryId];
      if(!parentSlug) return; // parent category missing or inactive — skip, don't crash

      subIdToSlug[s.id] = s.slug;
      CATALOGUE.subcategories[s.slug] = {
        name: s.name,
        parent: parentSlug,
        cover: mediaUrl(s.image) || ""
      };

      const cat = CATALOGUE.categories.find(c => c.id === parentSlug);
      if(cat) cat.subcategories.push(s.slug);
    });

    try{
      const prodRes = await Api.get("/products", { status: "active" });
      (prodRes.data || []).forEach(p => {
        const subSlug = subIdToSlug[p.subCategoryId];
        if(!subSlug) return; // parent sub category missing/inactive — skip, don't crash

        if(!CATALOGUE.products[subSlug]) CATALOGUE.products[subSlug] = [];
        CATALOGUE.products[subSlug].push({
          no: p.no,
          name: p.name,
          sku: p.sku,
          price: p.price,
          priceNote: p.priceNote,
          moq: p.moq,
          desc: p.shortDesc || "",
          imgSrc: mediaUrl((p.images && p.images[0]) || "") || ""
        });

        if(p.featured) CATALOGUE.featured.push([subSlug, p.no]);
      });
    }catch(err){
      console.error("Could not load products from the backend:", err.message);
    }
  }catch(err){
    console.error("Could not load sub categories from the backend:", err.message);
  }

  return CATALOGUE;
})();

/* MOQ (Minimum Order Quantity) — NOT present in the client's source PDFs.
   Derived as a sensible default: pack size mentioned in the product name
   (e.g. "Pack of 5" -> 5), else 1 for single-piece items.
   ⚠️ CLIENT: edit MOQ_OVERRIDES below with real per-SKU minimums whenever ready. */
const MOQ_OVERRIDES = {
  // "toran-3ft:Article-1": 10,
};
function getMOQ(subId, p){
  const key = `${subId}:${p.sku}`;
  if(MOQ_OVERRIDES[key] != null) return MOQ_OVERRIDES[key];
  const m = p.name && p.name.match(/pack of (\d+)/i);
  if(m) return parseInt(m[1], 10);
  return 1;
}

/* All products belonging to a category id, flattened across its subcategories */
function getCategoryProducts(catId){
  const cat = CATALOGUE.categories.find(c => c.id === catId);
  if(!cat) return [];
  const out = [];
  cat.subcategories.forEach(subId => {
    (CATALOGUE.products[subId] || []).forEach(p => out.push(getProduct(subId, p.no)));
  });
  return out;
}

function getProduct(subId, no) {
  const list = CATALOGUE.products[subId] || [];
  const p = list.find(x => x.no === no);
  if (!p) return null;
  return Object.assign({}, p, {
    subId,
    imgSrc: p.imgSrc || `assets/images/products/${subId}/${p.img}.png`,
    priceLabel: p.price != null ? `₹${p.price}` : (p.priceNote || "Ask on WhatsApp"),
    moq: p.moq != null ? p.moq : getMOQ(subId, p)
  });
}
