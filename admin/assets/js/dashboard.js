/* ==========================================================================
   BADARIYA FLOWERS — ADMIN DASHBOARD (dummy data for now)
   Every DUMMY_* block below is a stand-in for a future FastAPI response.
   Swap the fetchDummy() calls for real `fetch("/api/...")` calls later —
   the render functions already expect this exact shape.
   ========================================================================== */

(function(){

  const ICONS = {
    category: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M4 7h16M4 12h16M4 17h10"/></svg>',
    subcategory: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M9 6h11M9 12h11M9 18h11"/><circle cx="4" cy="6" r="1.6"/><circle cx="4" cy="12" r="1.6"/><circle cx="4" cy="18" r="1.6"/></svg>',
    product: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M20 7L12 3 4 7v10l8 4 8-4V7z"/><path d="M4 7l8 4 8-4M12 11v10"/></svg>',
    pdf: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M14 3H7a2 2 0 00-2 2v14a2 2 0 002 2h10a2 2 0 002-2V8z"/><path d="M14 3v5h5"/><path d="M9 13h6M9 17h6"/></svg>',
    plus: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 5v14M5 12h14"/></svg>',
    upload: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M12 16V4M6 10l6-6 6 6"/><path d="M4 20h16"/></svg>',
    tag: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M20.6 12.9L12.9 20.6a2 2 0 01-2.8 0l-6.7-6.7a2 2 0 010-2.8L11.1 3.4A2 2 0 0112.5 3H19a2 2 0 012 2v6.5a2 2 0 01-.6 1.4z"/><circle cx="14.5" cy="8.5" r="1.5"/></svg>',
    gear: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><circle cx="12" cy="12" r="3"/><path d="M4 12h2M18 12h2M12 4v2M12 18v2"/></svg>',
    arrow: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M5 12h14M13 6l6 6-6 6"/></svg>',
    wa: '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M17.5 14.4c-.3-.1-1.7-.9-2-1-.3-.1-.5-.1-.7.1-.2.3-.8 1-.9 1.1-.2.2-.3.2-.6.1-.3-.1-1.2-.4-2.3-1.4-.9-.8-1.4-1.7-1.6-2-.2-.3 0-.5.1-.6.1-.1.3-.3.4-.5.1-.1.2-.3.3-.5.1-.2 0-.4 0-.5C10.1 9 9.6 7.7 9.4 7.2c-.2-.5-.4-.4-.6-.4h-.5c-.2 0-.5.1-.7.3-.2.3-.9.9-.9 2.2s1 2.6 1.1 2.7c.1.2 2 3 4.8 4.2.7.3 1.2.5 1.6.6.7.2 1.3.2 1.8.1.6-.1 1.7-.7 1.9-1.3.2-.7.2-1.2.2-1.3-.1-.1-.3-.2-.6-.3z"/><path d="M12 2C6.5 2 2 6.5 2 12c0 1.9.5 3.7 1.5 5.3L2 22l4.8-1.5c1.5.9 3.3 1.3 5.2 1.3 5.5 0 10-4.5 10-10S17.5 2 12 2zm0 18.1c-1.7 0-3.3-.5-4.7-1.3l-.3-.2-3.2 1 1-3.1-.2-.3C3.6 15 3 13.5 3 12c0-5 4-9 9-9s9 4 9 9-4 9-9 9z"/></svg>',
    check: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M20 6L9 17l-5-5"/></svg>',
    box: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M20 7L12 3 4 7v10l8 4 8-4V7z"/></svg>',
    trash: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M4 7h16M9 7V5a2 2 0 012-2h2a2 2 0 012 2v2M6 7l1 13a2 2 0 002 2h6a2 2 0 002-2l1-13"/></svg>'
  };

  /* ---------------------------------------------------------------------
     DUMMY DATA — replace with API responses in Phase 3
     --------------------------------------------------------------------- */
  const DUMMY_STATS = [
    { key:"categories",    label:"Total Categories",     value:6,   icon:ICONS.category,    trend:"+0 this month",  flat:true },
    { key:"subcategories", label:"Total Sub Categories",  value:14,  icon:ICONS.subcategory, trend:"+2 this month" },
    { key:"products",      label:"Total Products",        value:186, icon:ICONS.product,     trend:"+9 this month" },
    { key:"pdfs",          label:"Catalogue PDFs",         value:11,  icon:ICONS.pdf,         trend:"Updated 2d ago", flat:true },
  ];

  const QUICK_ACTIONS = [
    { label:"Add Category",       sub:"Create a new product category",      icon:ICONS.tag,    href:"/admin/categories" },
    { label:"Add Product",        sub:"List a new design in the catalogue", icon:ICONS.plus,   href:"/admin/products" },
    { label:"Upload Catalogue PDF", sub:"Publish an updated price list",    icon:ICONS.upload, href:"catalogue.html" },
    { label:"Site Settings",      sub:"Contact info, WhatsApp, hours",      icon:ICONS.gear,   href:"/admin/settings" },
  ];

  const DUMMY_PRODUCTS = [
    { img:"../assets/images/products/toran-4ft/01.png", name:"Genda Toran — 4 Feet", sku:"BF-TOR-4FT-01", category:"Toran", price:"₹349", status:"active", date:"19 Jul 2026" },
    { img:"../assets/images/products/jhoomar/02.png",   name:"Marigold Jhoomar — 18\"", sku:"BF-JHM-18-02",  category:"Jhoomar", price:"₹599", status:"active", date:"18 Jul 2026" },
    { img:"../assets/images/products/haar-mala/03.png", name:"Haar Mala — Double Layer", sku:"BF-HAR-DL-03", category:"Haar Mala", price:"₹199", status:"low", date:"18 Jul 2026" },
    { img:"../assets/images/products/genda-big-latkan/01.png", name:"Genda Big Latkan", sku:"BF-LAT-BG-01", category:"Latkan", price:"₹129", status:"active", date:"17 Jul 2026" },
    { img:"../assets/images/products/wall-hanging/02.png", name:"Floral Wall Hanging", sku:"BF-WAL-02", category:"Wall Hanging", price:"₹449", status:"draft", date:"16 Jul 2026" },
  ];

  const STATUS_MAP = {
    active: { label:"Active",    cls:"admin-badge--success" },
    low:    { label:"Low Stock", cls:"admin-badge--warning" },
    draft:  { label:"Draft",     cls:"admin-badge--danger" },
  };

  const DUMMY_ACTIVITY = [
    { icon:ICONS.plus,  text:'<strong>New product added</strong> — Genda Toran 4 Feet', time:"10 minutes ago" },
    { icon:ICONS.wa,    text:'<strong>WhatsApp enquiry</strong> — Jhoomar 18" (customer in Jaipur)', time:"45 minutes ago" },
    { icon:ICONS.upload,text:'<strong>Catalogue PDF updated</strong> — Full Catalogue re-uploaded', time:"2 hours ago" },
    { icon:ICONS.tag,   text:'<strong>Sub category added</strong> — "Fancy Latkan" under Latkan', time:"5 hours ago" },
    { icon:ICONS.trash, text:'<strong>Product removed</strong> — Old Wall Hanging design (v1)', time:"Yesterday" },
    { icon:ICONS.check, text:'<strong>Order marked fulfilled</strong> — Bulk order, 40 Torans', time:"Yesterday" },
  ];

  const DUMMY_STATUS = [
    { label:"Website",           note:"Live and reachable",        state:"ok" },
    { label:"Database",          note:"Connected · MySQL",         state:"ok" },
    { label:"Catalogue Sync",    note:"1 PDF pending review",      state:"warn" },
    { label:"Last Backup",       note:"Completed 6 hours ago",     state:"ok" },
    { label:"WhatsApp API",      note:"Not configured yet",        state:"down" },
  ];

  /* ---------------------------------------------------------------------
     RENDERERS
     --------------------------------------------------------------------- */
  function renderStats(){
    const grid = document.getElementById("statGrid");
    if (!grid) return;
    grid.innerHTML = DUMMY_STATS.map(s => `
      <div class="stat-card">
        <div class="stat-card-top">
          <div class="stat-icon">${s.icon}</div>
          <span class="stat-trend${s.flat ? " is-flat" : ""}">${s.trend}</span>
        </div>
        <div class="stat-value">${s.value}</div>
        <div class="stat-label">${s.label}</div>
      </div>
    `).join("");
  }

  function renderQuickActions(){
    const wrap = document.getElementById("quickActions");
    if (!wrap) return;
    wrap.innerHTML = QUICK_ACTIONS.map(a => `
      <a class="quick-action-card" href="${a.href}">
        <div class="quick-action-icon">${a.icon}</div>
        <div class="quick-action-text"><strong>${a.label}</strong><span>${a.sub}</span></div>
        <span class="quick-action-arrow">${ICONS.arrow}</span>
      </a>
    `).join("");
  }

  function renderProductsTable(){
    const body = document.getElementById("recentProductsBody");
    if (!body) return;
    body.innerHTML = DUMMY_PRODUCTS.map(p => {
      const st = STATUS_MAP[p.status];
      return `
      <tr>
        <td>
          <div class="table-product-cell">
            <img src="${p.img}" alt="${p.name}">
            <div><strong>${p.name}</strong><span>${p.sku}</span></div>
          </div>
        </td>
        <td>${p.category}</td>
        <td class="table-price">${p.price}</td>
        <td><span class="admin-badge ${st.cls}"><span class="dot"></span>${st.label}</span></td>
        <td>${p.date}</td>
      </tr>`;
    }).join("");
  }

  function renderActivity(){
    const list = document.getElementById("activityList");
    if (!list) return;
    list.innerHTML = DUMMY_ACTIVITY.map(a => `
      <div class="activity-item">
        <div class="activity-icon">${a.icon}</div>
        <div class="activity-text"><p>${a.text}</p><time>${a.time}</time></div>
      </div>
    `).join("");
  }

  function renderStatus(){
    const list = document.getElementById("statusList");
    if (!list) return;
    list.innerHTML = DUMMY_STATUS.map(s => `
      <div class="status-row">
        <div class="status-row-left">
          <span class="status-dot ${s.state}"></span>
          <div><strong>${s.label}</strong><span>${s.note}</span></div>
        </div>
      </div>
    `).join("");
  }

  document.addEventListener("DOMContentLoaded", () => {
    renderStats();
    renderQuickActions();
    renderProductsTable();
    renderActivity();
    renderStatus();
  });

})();
