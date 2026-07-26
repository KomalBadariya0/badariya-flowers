/* ==========================================================================
   SUB-CATEGORIES.JS — Badariya Flowers Admin · Sub Categories Module
   ----------------------------------------------------------------------
   Written to be swapped onto a real backend with minimal changes:
     GET    /api/subcategories        -> SubCategoryAPI.list()
     GET    /api/subcategories/{id}   -> SubCategoryAPI.get(id)
     POST   /api/subcategories        -> SubCategoryAPI.create(payload)
     PUT    /api/subcategories/{id}   -> SubCategoryAPI.update(id, payload)
     DELETE /api/subcategories/{id}   -> SubCategoryAPI.remove(id)
     POST   /api/subcategories/upload -> SubCategoryAPI.uploadImage(file)
     GET    /api/categories           -> SubCategoryAPI.getCategories()

   Every SubCategoryAPI method already returns a Promise and already matches
   the shape a fetch() call would return, so the render / form / modal code
   below never needs to change when the dummy layer is replaced.

   RELATIONSHIP: Category -> Sub Category -> Product
   Every sub category row carries a `categoryId` that must reference a real
   row in the Categories module's store (bf_admin_categories_v1). The record
   shape mirrors the public site's CATALOGUE.subcategories entry (assets/js/
   catalog.js: name, parent) plus the `id`/slug is the exact subCategoryId
   key already used by the Products module (admin/assets/js/product_store.js
   -> ProductAPI.create() writes payload.subCategoryId using these same
   slugs, e.g. "toran-4ft"). Once FastAPI + MySQL land, Categories, Sub
   Categories and Products all read from the SAME `sub_categories` table
   instead of separate localStorage keys — this file is written so that
   swap is a pure data-layer change, no UI code changes required.
     admin field   -> public site field
     id            -> id (slug IS the sub category id used in
                       category.html?sub= and Products' subCategoryId)
     name          -> name
     categoryId    -> parent
     image         -> (subcategory cover, first product image today)
     status        -> controls whether the sub category is shown on the site
     sortOrder     -> display order under its parent category
   ========================================================================== */

   (function(){

    /* ============================================================
       DUMMY DATA LAYER
       Stands in for MySQL rows until FastAPI is wired up. Persisted
       to localStorage only so the demo survives a page refresh —
       replace this whole block with real fetch() calls later.
       ============================================================ */
    const STORAGE_KEY = "bf_admin_subcategories_v1";

    // Read-only mirror of the Categories module's own storage key so the
    // "Parent Category" dropdown always lists exactly what admin/categories.html
    // manages. Falls back to the same seed categories.js ships with, so the
    // dropdown still works even if nobody has opened the Categories page yet —
    // both files must be kept in sync by hand until a real /api/categories lands.
    const CATEGORIES_STORAGE_KEY = "bf_admin_categories_v1";
    const SEED_CATEGORIES_FALLBACK = [
      { id: "cat_toran", name: "Toran", slug: "toran", status: "active" },
      { id: "cat_latkans", name: "Latkans", slug: "latkans", status: "active" },
      { id: "cat_jhoomar", name: "Jhoomar", slug: "jhoomar", status: "active" },
      { id: "cat_haar_mala", name: "Haar Mala", slug: "haar-mala", status: "active" },
      { id: "cat_wall_hanging", name: "Wall Hangings", slug: "wall-hanging", status: "inactive" }
    ];

    function loadCategories(){
      try{
        const raw = localStorage.getItem(CATEGORIES_STORAGE_KEY);
        if(raw){
          const rows = JSON.parse(raw);
          if(Array.isArray(rows) && rows.length) return rows;
        }
      }catch(e){ /* fall through to fallback */ }
      return SEED_CATEGORIES_FALLBACK.slice();
    }

    // Seed slugs match the live subCategoryId keys already used across
    // catalog.js / product_store.js, so a fresh install of this module lines
    // up with real product data instead of inventing parallel IDs.
    const SEED_SUBCATEGORIES = [
      { id: "toran-3ft",         name: "3 Feet Toran",                    categoryId: "cat_toran",       slug: "toran-3ft",         image: "../assets/images/products/toran-3ft/01.png",         totalProducts: 24, status: "active", sortOrder: 1, createdAt: "2026-02-14" },
      { id: "toran-4ft",         name: "4 Feet Toran",                    categoryId: "cat_toran",       slug: "toran-4ft",         image: "../assets/images/products/toran-4ft/03.png",         totalProducts: 14, status: "active", sortOrder: 2, createdAt: "2026-02-14" },
      { id: "toran-6ft",         name: "6 Feet Toran",                    categoryId: "cat_toran",       slug: "toran-6ft",         image: "../assets/images/products/toran-6ft/03.png",         totalProducts: 8,  status: "active", sortOrder: 3, createdAt: "2026-02-14" },
      { id: "toran-10ft",        name: "10 Feet Toran",                   categoryId: "cat_toran",       slug: "toran-10ft",        image: "../assets/images/products/toran-10ft/09.png",        totalProducts: 10, status: "active", sortOrder: 4, createdAt: "2026-02-15" },
      { id: "genda-big-latkan",  name: "Genda Big Latkans",               categoryId: "cat_latkans",     slug: "genda-big-latkan",  image: "",                                                     totalProducts: 30, status: "active", sortOrder: 1, createdAt: "2026-02-15" },
      { id: "genda-3ft-latkan",  name: "Genda Fancy 3 Feet Latkans",      categoryId: "cat_latkans",     slug: "genda-3ft-latkan",  image: "../assets/images/products/genda-3ft-latkan/05.png",  totalProducts: 13, status: "active", sortOrder: 2, createdAt: "2026-02-15" },
      { id: "jj-latkan",         name: "JJ Latkan",                       categoryId: "cat_latkans",     slug: "jj-latkan",         image: "../assets/images/products/jj-latkan/01.png",         totalProducts: 23, status: "active", sortOrder: 3, createdAt: "2026-02-16" },
      { id: "jhoomar",           name: "Jhoomar",                         categoryId: "cat_jhoomar",     slug: "jhoomar",           image: "../assets/images/products/jhoomar/19.png",            totalProducts: 25, status: "active", sortOrder: 1, createdAt: "2026-02-16" },
      { id: "jhoomar-2",         name: "Jhoomar 2",                       categoryId: "cat_jhoomar",     slug: "jhoomar-2",         image: "../assets/images/products/jhoomar-2/21.png",         totalProducts: 21, status: "active", sortOrder: 2, createdAt: "2026-02-17" },
      { id: "haar-mala",         name: "Haar Mala",                       categoryId: "cat_haar_mala",   slug: "haar-mala",         image: "../assets/images/products/haar-mala/05.png",         totalProducts: 5,  status: "active", sortOrder: 1, createdAt: "2026-02-17" },
      { id: "wall-hanging",      name: "Wall Hanging",                    categoryId: "cat_wall_hanging",slug: "wall-hanging",      image: "../assets/images/products/wall-hanging/11.png",      totalProducts: 11, status: "inactive", sortOrder: 1, createdAt: "2026-03-02" }
    ];

    function loadStore(){
      try{
        const raw = localStorage.getItem(STORAGE_KEY);
        if(raw) return JSON.parse(raw);
      }catch(e){ /* fall through to seed */ }
      saveStore(SEED_SUBCATEGORIES);
      return SEED_SUBCATEGORIES.slice();
    }
    function saveStore(rows){
      localStorage.setItem(STORAGE_KEY, JSON.stringify(rows));
    }
    function delay(ms){ return new Promise(res => setTimeout(res, ms)); }
    function genId(){ return "subcat_" + Date.now().toString(36) + Math.random().toString(36).slice(2, 6); }

    /* ============================================================
       SubCategoryAPI — swap the body of each method for a fetch() call
       against FastAPI. Signatures and return shapes are designed to
       stay identical, so nothing above this layer needs to change.
       ============================================================ */
    const SubCategoryAPI = {
      async list(params = {}){
        // Future: const res = await fetch("/api/subcategories?" + new URLSearchParams(params));
        //         return res.json();
        await delay(260);
        let rows = loadStore();
        if(params.search){
          const q = params.search.toLowerCase();
          rows = rows.filter(s => s.name.toLowerCase().includes(q) || s.slug.toLowerCase().includes(q));
        }
        if(params.categoryId && params.categoryId !== "all"){
          rows = rows.filter(s => s.categoryId === params.categoryId);
        }
        rows = rows.slice().sort((a, b) => a.sortOrder - b.sortOrder);
        return { data: rows, total: rows.length };
      },

      async get(id){
        // Future: const res = await fetch(`/api/subcategories/${id}`); return res.json();
        await delay(150);
        const row = loadStore().find(s => s.id === id);
        if(!row) throw new Error("Sub category not found");
        return row;
      },

      async create(payload){
        // Future: const res = await fetch("/api/subcategories", { method:"POST", headers:{...}, body: JSON.stringify(payload) });
        //         if(!res.ok) throw new Error((await res.json()).detail); return res.json();
        await delay(300);
        const rows = loadStore();
        if(rows.some(s => s.slug === payload.slug)){
          const err = new Error("A sub category with this slug already exists");
          err.field = "slug";
          throw err;
        }
        if(rows.some(s => s.categoryId === payload.categoryId && s.name.toLowerCase() === payload.name.toLowerCase())){
          const err = new Error("This category already has a sub category with this name");
          err.field = "name";
          throw err;
        }
        const row = {
          id: genId(),
          name: payload.name,
          categoryId: payload.categoryId,
          slug: payload.slug,
          image: payload.image || "",
          totalProducts: 0,
          status: payload.status || "active",
          sortOrder: Number(payload.sortOrder) || rows.length + 1,
          createdAt: new Date().toISOString().slice(0, 10)
        };
        rows.push(row);
        saveStore(rows);
        return row;
      },

      async update(id, payload){
        // Future: const res = await fetch(`/api/subcategories/${id}`, { method:"PUT", headers:{...}, body: JSON.stringify(payload) });
        //         if(!res.ok) throw new Error((await res.json()).detail); return res.json();
        await delay(300);
        const rows = loadStore();
        const idx = rows.findIndex(s => s.id === id);
        if(idx === -1) throw new Error("Sub category not found");

        if(rows.some(s => s.id !== id && s.slug === payload.slug)){
          const err = new Error("A sub category with this slug already exists");
          err.field = "slug";
          throw err;
        }
        if(rows.some(s => s.id !== id && s.categoryId === payload.categoryId && s.name.toLowerCase() === payload.name.toLowerCase())){
          const err = new Error("This category already has a sub category with this name");
          err.field = "name";
          throw err;
        }

        rows[idx] = {
          ...rows[idx],
          name: payload.name,
          categoryId: payload.categoryId,
          slug: payload.slug,
          image: payload.image || rows[idx].image,
          status: payload.status || rows[idx].status,
          sortOrder: Number(payload.sortOrder) || rows[idx].sortOrder
        };
        saveStore(rows);
        return rows[idx];
      },

      async remove(id){
        // Future: const res = await fetch(`/api/subcategories/${id}`, { method:"DELETE" }); return res.ok;
        await delay(250);
        const rows = loadStore();
        const next = rows.filter(s => s.id !== id);
        saveStore(next);
        return true;
      },

      async uploadImage(file){
        // Future: const fd = new FormData(); fd.append("file", file);
        //         const res = await fetch("/api/subcategories/upload", { method:"POST", body: fd });
        //         return (await res.json()).url;
        return new Promise((resolve, reject) => {
          const reader = new FileReader();
          reader.onload = () => resolve(reader.result); // base64 data URL stand-in for a real uploaded file URL
          reader.onerror = () => reject(new Error("Could not read image"));
          reader.readAsDataURL(file);
        });
      },

      /* Read-only taxonomy helper — sourced from the Categories module's own
         store so a sub category can only ever attach to a category that
         really exists in Admin > Categories. */
      async getCategories(){
        // Future: const res = await fetch("/api/categories"); return res.json();
        await delay(120);
        return loadCategories();
      }
    };

    /* ============================================================
       STATE
       ============================================================ */
    const state = {
      rows: [],
      categories: [],
      search: "",
      categoryFilter: "all",
      editingId: null,
      deletingId: null,
      uploadedImage: null,
      slugTouched: false
    };

    /* ============================================================
       DOM REFS
       ============================================================ */
    const tbody = document.getElementById("subcatTableBody");
    const emptyState = document.getElementById("subcatEmptyState");
    const searchInput = document.getElementById("subcatSearchInput");
    const categoryFilterSelect = document.getElementById("subcatCategoryFilter");

    const formModal = document.getElementById("subcatFormModal");
    const form = document.getElementById("subcatForm");
    const formTitle = document.getElementById("subcatFormTitle");
    const parentCategorySelect = document.getElementById("subcatParentCategory");
    const nameInput = document.getElementById("subcatName");
    const slugInput = document.getElementById("subcatSlug");
    const slugAutoToggle = document.getElementById("subcatSlugAutoToggle");
    const statusSelect = document.getElementById("subcatStatus");
    const sortOrderInput = document.getElementById("subcatSortOrder");
    const imageInput = document.getElementById("subcatImageInput");
    const imageDrop = document.getElementById("subcatImageDrop");
    const imagePreview = document.getElementById("subcatImagePreview");
    const imageRemoveBtn = document.getElementById("subcatImageRemoveBtn");

    const viewModal = document.getElementById("subcatViewModal");
    const deleteModal = document.getElementById("subcatDeleteModal");
    const toast = document.getElementById("subcatToast");
    const toastMsg = document.getElementById("subcatToastMsg");

    /* ============================================================
       HELPERS
       ============================================================ */
    function slugify(text){
      return text
        .toString().trim().toLowerCase()
        .replace(/[^a-z0-9\s-]/g, "")
        .replace(/\s+/g, "-")
        .replace(/-+/g, "-")
        .replace(/^-|-$/g, "");
    }

    function formatDate(iso){
      if(!iso) return "—";
      const d = new Date(iso);
      if(Number.isNaN(d.getTime())) return iso;
      return d.toLocaleDateString("en-IN", { day: "2-digit", month: "short", year: "numeric" });
    }

    function categoryName(categoryId){
      const cat = state.categories.find(c => c.id === categoryId);
      return cat ? cat.name : "Unknown Category";
    }

    function showToast(message, type = "success"){
      toastMsg.textContent = message;
      toast.classList.remove("is-error", "is-success");
      toast.classList.add(type === "error" ? "is-error" : "is-success");
      toast.classList.add("is-open");
      clearTimeout(showToast._t);
      showToast._t = setTimeout(() => toast.classList.remove("is-open"), 2600);
    }

    function openModal(modal){ modal.classList.add("is-open"); document.body.style.overflow = "hidden"; }
    function closeModal(modal){ modal.classList.remove("is-open"); document.body.style.overflow = ""; }

    function clearFieldErrors(){
      document.getElementById("subcatParentCategoryError").textContent = "";
      document.getElementById("subcatNameError").textContent = "";
      document.getElementById("subcatSlugError").textContent = "";
      parentCategorySelect.classList.remove("is-invalid");
      nameInput.classList.remove("is-invalid");
      slugInput.classList.remove("is-invalid");
    }

    function fieldRefFor(field){
      if(field === "categoryId") return { el: document.getElementById("subcatParentCategoryError"), input: parentCategorySelect };
      if(field === "slug") return { el: document.getElementById("subcatSlugError"), input: slugInput };
      return { el: document.getElementById("subcatNameError"), input: nameInput };
    }

    function setFieldError(field, message){
      const { el, input } = fieldRefFor(field);
      if(el) el.textContent = message;
      if(input) input.classList.add("is-invalid");
    }

    /* ============================================================
       PARENT CATEGORY DROPDOWNS (toolbar filter + form select)
       ============================================================ */
    function populateCategoryDropdowns(){
      const activeCats = state.categories.filter(c => c.status !== "inactive");
      const allCats = state.categories;

      const filterOptions = ['<option value="all">All Categories</option>']
        .concat(allCats.map(c => `<option value="${c.id}">${c.name}</option>`));
      categoryFilterSelect.innerHTML = filterOptions.join("");
      categoryFilterSelect.value = state.categoryFilter;

      const formOptions = ['<option value="">Select a category…</option>']
        .concat(allCats.map(c => `<option value="${c.id}">${c.name}${c.status === "inactive" ? " (inactive)" : ""}</option>`));
      parentCategorySelect.innerHTML = formOptions.join("");

      if(!allCats.length){
        showToast("No categories found — add a category first in Admin > Categories", "error");
      }
      void activeCats; // reserved for a future "hide inactive categories" toggle
    }

    /* ============================================================
       RENDER — TABLE
       ============================================================ */
    function skeletonRows(count = 4){
      return Array.from({ length: count }).map(() => `
        <tr>
          <td><div class="subcat-skeleton-bar" style="width:46px;height:46px;border-radius:10px;"></div></td>
          <td><div class="subcat-skeleton-bar" style="width:130px;"></div></td>
          <td><div class="subcat-skeleton-bar" style="width:90px;"></div></td>
          <td><div class="subcat-skeleton-bar" style="width:80px;"></div></td>
          <td><div class="subcat-skeleton-bar" style="width:40px;"></div></td>
          <td><div class="subcat-skeleton-bar" style="width:70px;"></div></td>
          <td><div class="subcat-skeleton-bar" style="width:90px;"></div></td>
          <td><div class="subcat-skeleton-bar" style="width:60px;margin-left:auto;"></div></td>
        </tr>`).join("");
    }

    function rowTemplate(sub){
      const isActive = sub.status === "active";
      return `
      <tr data-id="${sub.id}">
        <td>
          ${sub.image
            ? `<img class="subcat-img-cell" src="${sub.image}" alt="${sub.name}">`
            : `<div class="subcat-img-cell" style="display:flex;align-items:center;justify-content:center;color:var(--accent);">
                 <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.6"><rect x="3" y="5" width="18" height="14" rx="2"/><circle cx="9" cy="10" r="1.6"/><path d="M21 16l-5.5-5.5L4 21"/></svg>
               </div>`}
        </td>
        <td>
          <div class="subcat-name-cell"><strong>${sub.name}</strong></div>
        </td>
        <td><span class="subcat-parent-pill"><span class="dot"></span>${categoryName(sub.categoryId)}</span></td>
        <td><span class="subcat-slug-pill">${sub.slug}</span></td>
        <td><span class="subcat-products-count">${sub.totalProducts}</span></td>
        <td>
          <button type="button" class="admin-badge subcat-status-toggle ${isActive ? "admin-badge--success" : "admin-badge--danger"}" data-action="toggle-status" data-id="${sub.id}">
            <span class="dot"></span>${isActive ? "Active" : "Inactive"}
          </button>
        </td>
        <td>${formatDate(sub.createdAt)}</td>
        <td>
          <div class="subcat-actions-cell">
            <button class="subcat-action-btn" type="button" data-action="view" data-id="${sub.id}" aria-label="View ${sub.name}">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M1 12s4-7 11-7 11 7 11 7-4 7-11 7-11-7-11-7z"/><circle cx="12" cy="12" r="3"/></svg>
            </button>
            <button class="subcat-action-btn" type="button" data-action="edit" data-id="${sub.id}" aria-label="Edit ${sub.name}">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M12 20h9"/><path d="M16.5 3.5a2.1 2.1 0 013 3L7 19l-4 1 1-4z"/></svg>
            </button>
            <button class="subcat-action-btn is-danger" type="button" data-action="delete" data-id="${sub.id}" aria-label="Delete ${sub.name}">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M3 6h18M8 6V4a1 1 0 011-1h6a1 1 0 011 1v2m3 0l-1 14a2 2 0 01-2 2H7a2 2 0 01-2-2L4 6"/></svg>
            </button>
          </div>
        </td>
      </tr>`;
    }

    function renderRows(rows){
      tbody.innerHTML = rows.map(rowTemplate).join("");
      emptyState.hidden = rows.length !== 0;
    }

    /* ============================================================
       LOAD / REFRESH — talks to SubCategoryAPI, never the storage layer
       ============================================================ */
    async function refresh(){
      tbody.innerHTML = skeletonRows();
      emptyState.hidden = true;
      try{
        const [{ data }, categories] = await Promise.all([
          SubCategoryAPI.list({ search: state.search, categoryId: state.categoryFilter }),
          SubCategoryAPI.getCategories()
        ]);
        state.categories = categories;
        state.rows = data;
        populateCategoryDropdowns();
        renderRows(data);
      }catch(err){
        showToast(err.message || "Could not load sub categories", "error");
        renderRows([]);
      }
    }

    /* ============================================================
       SEARCH + FILTER (live)
       ============================================================ */
    let searchDebounce;
    searchInput.addEventListener("input", () => {
      clearTimeout(searchDebounce);
      searchDebounce = setTimeout(() => {
        state.search = searchInput.value.trim();
        refresh();
      }, 200);
    });
    categoryFilterSelect.addEventListener("change", () => {
      state.categoryFilter = categoryFilterSelect.value;
      refresh();
    });

    /* ============================================================
       FORM MODAL — ADD / EDIT
       ============================================================ */
    function resetForm(){
      form.reset();
      clearFieldErrors();
      state.editingId = null;
      state.uploadedImage = null;
      state.slugTouched = false;
      slugAutoToggle.classList.add("is-active");
      document.getElementById("subcatId").value = "";
      parentCategorySelect.value = "";
      statusSelect.value = "active";
      sortOrderInput.value = state.rows.length + 1;
      imagePreview.innerHTML = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><rect x="3" y="5" width="18" height="14" rx="2"/><circle cx="9" cy="10" r="1.6"/><path d="M21 16l-5.5-5.5L4 21"/></svg>`;
      imageRemoveBtn.hidden = true;
    }

    function openAddModal(){
      if(!state.categories.length){
        showToast("Add a category first in Admin > Categories", "error");
        return;
      }
      resetForm();
      formTitle.textContent = "Add Sub Category";
      document.getElementById("subcatFormSave").textContent = "Save Sub Category";
      openModal(formModal);
      parentCategorySelect.focus();
    }

    async function openEditModal(id){
      resetForm();
      try{
        const sub = await SubCategoryAPI.get(id);
        formTitle.textContent = "Edit Sub Category";
        document.getElementById("subcatFormSave").textContent = "Save Changes";
        document.getElementById("subcatId").value = sub.id;
        parentCategorySelect.value = sub.categoryId;
        nameInput.value = sub.name;
        slugInput.value = sub.slug;
        statusSelect.value = sub.status;
        sortOrderInput.value = sub.sortOrder;
        state.editingId = sub.id;
        state.slugTouched = true; // editing an existing slug shouldn't silently auto-change
        slugAutoToggle.classList.remove("is-active");
        if(sub.image){
          state.uploadedImage = sub.image;
          imagePreview.innerHTML = `<img src="${sub.image}" alt="${sub.name}">`;
          imageRemoveBtn.hidden = false;
        }
        openModal(formModal);
      }catch(err){
        showToast(err.message || "Could not load sub category", "error");
      }
    }

    function closeFormModal(){
      closeModal(formModal);
      resetForm();
    }

    document.getElementById("openAddSubcatBtn").addEventListener("click", openAddModal);
    document.getElementById("subcatFormClose").addEventListener("click", closeFormModal);
    document.getElementById("subcatFormCancel").addEventListener("click", closeFormModal);
    formModal.addEventListener("click", (e) => { if(e.target === formModal) closeFormModal(); });

    /* ---- slug auto-generate ---- */
    nameInput.addEventListener("input", () => {
      if(!state.slugTouched){
        slugInput.value = slugify(nameInput.value);
      }
    });
    slugInput.addEventListener("input", () => {
      state.slugTouched = true;
      slugAutoToggle.classList.remove("is-active");
    });
    slugAutoToggle.addEventListener("click", () => {
      state.slugTouched = false;
      slugAutoToggle.classList.add("is-active");
      slugInput.value = slugify(nameInput.value);
    });

    /* ---- image upload + preview + remove ---- */
    imageDrop.addEventListener("click", (e) => {
      if(e.target.closest("#subcatImageRemoveBtn")) return;
      imageInput.click();
    });
    imageInput.addEventListener("change", async () => {
      const file = imageInput.files[0];
      if(!file) return;
      if(file.size > 2 * 1024 * 1024){
        showToast("Image must be under 2MB", "error");
        imageInput.value = "";
        return;
      }
      try{
        const url = await SubCategoryAPI.uploadImage(file);
        state.uploadedImage = url;
        imagePreview.innerHTML = `<img src="${url}" alt="Sub category preview">`;
        imageRemoveBtn.hidden = false;
      }catch(err){
        showToast(err.message || "Could not read image", "error");
      }
    });
    imageRemoveBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      state.uploadedImage = null;
      imageInput.value = "";
      imagePreview.innerHTML = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><rect x="3" y="5" width="18" height="14" rx="2"/><circle cx="9" cy="10" r="1.6"/><path d="M21 16l-5.5-5.5L4 21"/></svg>`;
      imageRemoveBtn.hidden = true;
    });

    /* ---- submit (create or update) ---- */
    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      clearFieldErrors();

      const payload = {
        categoryId: parentCategorySelect.value,
        name: nameInput.value.trim(),
        slug: slugify(slugInput.value.trim()),
        status: statusSelect.value,
        sortOrder: sortOrderInput.value,
        image: state.uploadedImage
      };

      let hasError = false;
      if(!payload.categoryId){
        setFieldError("categoryId", "Please select a parent category");
        hasError = true;
      }
      if(!payload.name){
        setFieldError("name", "Sub category name is required");
        hasError = true;
      }
      if(!payload.slug){
        setFieldError("slug", "Slug is required");
        hasError = true;
      }
      if(hasError) return;

      const saveBtn = document.getElementById("subcatFormSave");
      const originalLabel = saveBtn.textContent;
      saveBtn.disabled = true;
      saveBtn.textContent = "Saving…";

      try{
        if(state.editingId){
          await SubCategoryAPI.update(state.editingId, payload);
          showToast("Sub category updated successfully");
        }else{
          await SubCategoryAPI.create(payload);
          showToast("Sub category added successfully");
        }
        closeFormModal();
        refresh();
      }catch(err){
        if(err.field){
          setFieldError(err.field, err.message);
        }else{
          showToast(err.message || "Could not save sub category", "error");
        }
      }finally{
        saveBtn.disabled = false;
        saveBtn.textContent = originalLabel;
      }
    });

    /* ============================================================
       VIEW MODAL
       ============================================================ */
    async function openViewModal(id){
      try{
        const sub = await SubCategoryAPI.get(id);
        document.getElementById("viewSubcatImage").src = sub.image || "";
        document.getElementById("viewSubcatImage").alt = sub.name;
        document.getElementById("viewSubcatName").textContent = sub.name;
        document.getElementById("viewSubcatSlug").textContent = sub.slug;
        document.getElementById("viewSubcatParent").textContent = categoryName(sub.categoryId);
        document.getElementById("viewSubcatProducts").textContent = sub.totalProducts;
        document.getElementById("viewSubcatStatus").textContent = sub.status === "active" ? "Active" : "Inactive";
        document.getElementById("viewSubcatSortOrder").textContent = sub.sortOrder;
        document.getElementById("viewSubcatCreated").textContent = formatDate(sub.createdAt);
        openModal(viewModal);
      }catch(err){
        showToast(err.message || "Could not load sub category", "error");
      }
    }
    document.getElementById("subcatViewClose").addEventListener("click", () => closeModal(viewModal));
    document.getElementById("subcatViewCloseBtn").addEventListener("click", () => closeModal(viewModal));
    viewModal.addEventListener("click", (e) => { if(e.target === viewModal) closeModal(viewModal); });

    /* ============================================================
       DELETE MODAL
       ============================================================ */
    function openDeleteModal(id, name){
      state.deletingId = id;
      document.getElementById("deleteSubcatName").textContent = name;
      openModal(deleteModal);
    }
    document.getElementById("subcatDeleteCancel").addEventListener("click", () => closeModal(deleteModal));
    deleteModal.addEventListener("click", (e) => { if(e.target === deleteModal) closeModal(deleteModal); });

    document.getElementById("subcatDeleteConfirm").addEventListener("click", async () => {
      if(!state.deletingId) return;
      const btn = document.getElementById("subcatDeleteConfirm");
      btn.disabled = true;
      btn.textContent = "Deleting…";
      try{
        await SubCategoryAPI.remove(state.deletingId);
        showToast("Sub category deleted");
        closeModal(deleteModal);
        refresh();
      }catch(err){
        showToast(err.message || "Could not delete sub category", "error");
      }finally{
        btn.disabled = false;
        btn.textContent = "Delete Sub Category";
        state.deletingId = null;
      }
    });

    /* ============================================================
       TABLE ACTIONS (event delegation)
       ============================================================ */
    tbody.addEventListener("click", async (e) => {
      const btn = e.target.closest("[data-action]");
      if(!btn) return;
      const id = btn.dataset.id;
      const action = btn.dataset.action;
      const sub = state.rows.find(s => s.id === id);

      if(action === "view") openViewModal(id);
      if(action === "edit") openEditModal(id);
      if(action === "delete" && sub) openDeleteModal(id, sub.name);

      if(action === "toggle-status" && sub){
        const nextStatus = sub.status === "active" ? "inactive" : "active";
        btn.disabled = true;
        try{
          await SubCategoryAPI.update(id, { ...sub, status: nextStatus });
          showToast(`Sub category marked ${nextStatus === "active" ? "Active" : "Inactive"}`);
          refresh();
        }catch(err){
          showToast(err.message || "Could not update status", "error");
          btn.disabled = false;
        }
      }
    });

    /* ============================================================
       ESC closes any open modal
       ============================================================ */
    document.addEventListener("keydown", (e) => {
      if(e.key !== "Escape") return;
      [formModal, viewModal, deleteModal].forEach(m => { if(m.classList.contains("is-open")) closeModal(m); });
    });

    /* ============================================================
       BOOT
       ============================================================ */
    document.addEventListener("DOMContentLoaded", refresh);

  })();
