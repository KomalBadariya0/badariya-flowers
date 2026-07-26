/* ==========================================================================
   BADARIYA FLOWERS — ADMIN SHELL (shared across every admin page)

   HOW TO REUSE THIS ON A NEW ADMIN PAGE
   1. Copy the <head> block from dashboard.html (fonts + style.css +
      responsive.css + admin.css + <page>.css).
   2. In <body data-admin-page="categories">, add two empty mount points:
        <div id="adminSidebarMount"></div>
        <div id="adminTopbarMount"></div>
      then your <main class="admin-main"><div class="admin-content">...</div></main>
      wrapper (see dashboard.html for the exact shell markup).
   3. Set body's data-admin-page to the nav key you want highlighted
      (dashboard | categories | subcategories | products | catalogue | settings).
   4. Include this file (admin.js) before your page-specific script.
   The same markup also lives in /admin/layout/sidebar.html as a plain
   reference partial (handy later if this becomes a FastAPI/Jinja include).
   ========================================================================== */

   (function(){

    const NAV_ITEMS = [
      { key:"dashboard",    label:"Dashboard",        href:"/admin/dashboard.html",
        icon:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><rect x="3" y="3" width="8" height="8" rx="2"/><rect x="13" y="3" width="8" height="5" rx="2"/><rect x="13" y="12" width="8" height="9" rx="2"/><rect x="3" y="14" width="8" height="7" rx="2"/></svg>' },
      { key:"categories",   label:"Categories",       href:"/admin/categories",
        icon:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M4 7h16M4 12h16M4 17h10"/></svg>' },
      { key:"subcategories",label:"Sub Categories",   href:"/admin/subcategories",
        icon:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M9 6h11M9 12h11M9 18h11"/><circle cx="4" cy="6" r="1.6"/><circle cx="4" cy="12" r="1.6"/><circle cx="4" cy="18" r="1.6"/></svg>' },
      { key:"products",     label:"Products",         href:"/admin/products",
        icon:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M20 7L12 3 4 7v10l8 4 8-4V7z"/><path d="M4 7l8 4 8-4M12 11v10"/></svg>' },
      { key:"catalogue",    label:"Catalogue PDF",    href:"/admin/catalogue",
        icon:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M14 3H7a2 2 0 00-2 2v14a2 2 0 002 2h10a2 2 0 002-2V8z"/><path d="M14 3v5h5"/><path d="M9 13h6M9 17h6"/></svg>' },
    ];
  
    const NAV_BOTTOM = [
      { key:"settings", label:"Settings", href:"/admin/settings",
        icon:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.7 1.7 0 00.34 1.87l.06.06a2 2 0 11-2.83 2.83l-.06-.06a1.7 1.7 0 00-1.87-.34 1.7 1.7 0 00-1 1.55V21a2 2 0 11-4 0v-.09a1.7 1.7 0 00-1-1.55 1.7 1.7 0 00-1.87.34l-.06.06a2 2 0 11-2.83-2.83l.06-.06a1.7 1.7 0 00.34-1.87 1.7 1.7 0 00-1.55-1H3a2 2 0 110-4h.09a1.7 1.7 0 001.55-1 1.7 1.7 0 00-.34-1.87l-.06-.06a2 2 0 112.83-2.83l.06.06a1.7 1.7 0 001.87.34H9a1.7 1.7 0 001-1.55V3a2 2 0 114 0v.09a1.7 1.7 0 001 1.55 1.7 1.7 0 001.87-.34l.06-.06a2 2 0 112.83 2.83l-.06.06a1.7 1.7 0 00-.34 1.87V9a1.7 1.7 0 001.55 1H21a2 2 0 110 4h-.09a1.7 1.7 0 00-1.55 1z"/></svg>' },
    ];
  
    function navLinkHTML(item, activeKey){
      const active = item.key === activeKey ? " is-active" : "";
      return `<a href="${item.href}" class="admin-nav-link${active}" data-nav="${item.key}">${item.icon}<span>${item.label}</span></a>`;
    }
  
    function sidebarHTML(activeKey){
      return `
      <aside class="admin-sidebar" id="adminSidebar">
        <div class="admin-sidebar-glow"></div>
        <a href="/admin/dashboard.html" class="admin-brand">
          <img src="../assets/images/logo/logo.png" alt="Badariya Flowers logo">
          <span class="admin-brand-text"><strong>Badariya Flowers</strong><span>Admin Panel</span></span>
        </a>
        <svg class="admin-scallop" viewBox="0 0 260 14" preserveAspectRatio="none" aria-hidden="true">
          <path d="M0,0 H260 V5 C240,13 220,2 200,10 C180,2 160,13 140,5 C120,13 100,2 80,10 C60,2 40,13 20,5 C10,9 5,11 0,10 Z"></path>
        </svg>
        <nav class="admin-nav" aria-label="Admin navigation">
          ${NAV_ITEMS.map(item => navLinkHTML(item, activeKey)).join("")}
          <div class="admin-nav-label">System</div>
          ${NAV_BOTTOM.map(item => navLinkHTML(item, activeKey)).join("")}
        </nav>
        <div class="admin-sidebar-footer">
          <a href="../index.html" class="admin-nav-link" id="adminLogout">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4"/><path d="M16 17l5-5-5-5"/><path d="M21 12H9"/></svg>
            <span>Logout</span>
          </a>
        </div>
      </aside>`;
    }
  
    function topbarHTML(pageTitle){
      return `
      <header class="admin-topbar">
        <button class="admin-topbar-toggle" id="sidebarCollapseBtn" aria-label="Toggle sidebar" title="Toggle sidebar">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 6h16M4 12h16M4 18h16"/></svg>
        </button>
  
        <div class="admin-search">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="7"/><path d="M21 21l-4.3-4.3"/></svg>
          <input type="text" placeholder="Search products, categories, orders…" aria-label="Search">
        </div>
  
        <div class="admin-topbar-spacer"></div>
  
        <div class="admin-topbar-actions">
          <div style="position:relative;">
            <button class="admin-icon-btn" id="notifBtn" aria-label="Notifications">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M18 8a6 6 0 10-12 0c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.7 21a2 2 0 01-3.4 0"/></svg>
              <span class="dot"></span>
            </button>
            <div class="admin-dropdown" id="notifDropdown" style="width:260px;">
              <div class="admin-dropdown-head"><strong>Notifications</strong><span>3 new updates</span></div>
              <div class="admin-notif-item"><strong>New enquiry received</strong><span>WhatsApp enquiry for Jhoomar 18" — 5m ago</span></div>
              <div class="admin-notif-item"><strong>Catalogue PDF updated</strong><span>Full catalogue re-uploaded — 2h ago</span></div>
              <div class="admin-notif-item"><strong>Low stock flagged</strong><span>Genda Big Latkan running low — 1d ago</span></div>
            </div>
          </div>
  
          <div class="admin-profile" id="profileBtn">
            <div class="admin-avatar">BF</div>
            <div class="admin-profile-text"><strong>Badariya Admin</strong><span>Owner</span></div>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M6 9l6 6 6-6"/></svg>
            <div class="admin-dropdown" id="profileDropdown">
              <div class="admin-dropdown-head"><strong>Badariya Admin</strong><span>admin@badariyaflowers.com</span></div>
              <a href="/admin/settings"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><circle cx="12" cy="12" r="3"/><path d="M4 12h2M18 12h2M12 4v2M12 18v2"/></svg>Account settings</a>
              <button type="button" class="danger"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4"/><path d="M16 17l5-5-5-5"/><path d="M21 12H9"/></svg>Logout</button>
            </div>
          </div>
        </div>
      </header>`;
    }
  
    function renderShell(){
      const sidebarMount = document.getElementById("adminSidebarMount");
      const topbarMount = document.getElementById("adminTopbarMount");
      const activeKey = document.body.getAttribute("data-admin-page") || "dashboard";
      if (sidebarMount) sidebarMount.outerHTML = sidebarHTML(activeKey) + '<div class="admin-overlay" id="adminOverlay"></div>';
      if (topbarMount) topbarMount.outerHTML = topbarHTML();
    }
  
    function initInteractions(){
      const shell = document.querySelector(".admin-shell");
      const sidebar = document.getElementById("adminSidebar");
      const overlay = document.getElementById("adminOverlay");
      const collapseBtn = document.getElementById("sidebarCollapseBtn");
  
      // Desktop collapse (persists across pages)
      const COLLAPSE_KEY = "bf_admin_sidebar_collapsed";
      if (localStorage.getItem(COLLAPSE_KEY) === "1" && window.innerWidth > 992){
        shell.classList.add("is-collapsed");
        sidebar.classList.add("is-collapsed");
      }
  
      function openMobileSidebar(){
        sidebar.classList.add("is-mobile-open");
        overlay.classList.add("is-open");
        document.body.classList.add("admin-scroll-lock");
      }
      function closeMobileSidebar(){
        sidebar.classList.remove("is-mobile-open");
        overlay.classList.remove("is-open");
        document.body.classList.remove("admin-scroll-lock");
      }
  
      collapseBtn?.addEventListener("click", () => {
        if (window.innerWidth <= 992){
          // mobile: open/close off-canvas drawer
          if (sidebar.classList.contains("is-mobile-open")) closeMobileSidebar();
          else openMobileSidebar();
        } else {
          shell.classList.toggle("is-collapsed");
          sidebar.classList.toggle("is-collapsed");
          localStorage.setItem(COLLAPSE_KEY, shell.classList.contains("is-collapsed") ? "1" : "0");
        }
      });
  
      overlay?.addEventListener("click", closeMobileSidebar);
  
      // ESC closes the mobile drawer
      document.addEventListener("keydown", (e) => {
        if (e.key === "Escape" && sidebar?.classList.contains("is-mobile-open")) closeMobileSidebar();
      });
  
      // Closing the drawer via a nav link tap (and the safety-net resize
      // handler below) should also release the scroll lock.
      window.addEventListener("resize", () => {
        if (window.innerWidth > 992 && sidebar?.classList.contains("is-mobile-open")) closeMobileSidebar();
      });
  
      // Dropdowns
      function setupDropdown(btnId, dropdownId){
        const btn = document.getElementById(btnId);
        const dropdown = document.getElementById(dropdownId);
        if (!btn || !dropdown) return;
        btn.addEventListener("click", (e) => {
          e.stopPropagation();
          const willOpen = !dropdown.classList.contains("is-open");
          document.querySelectorAll(".admin-dropdown.is-open").forEach(d => d.classList.remove("is-open"));
          if (willOpen) dropdown.classList.add("is-open");
        });
      }
      setupDropdown("notifBtn", "notifDropdown");
      setupDropdown("profileBtn", "profileDropdown");
      document.addEventListener("click", () => {
        document.querySelectorAll(".admin-dropdown.is-open").forEach(d => d.classList.remove("is-open"));
      });
  
      // Topbar shadow on scroll
      const topbar = document.querySelector(".admin-topbar");
      window.addEventListener("scroll", () => {
        if (!topbar) return;
        topbar.style.boxShadow = window.scrollY > 6 ? "0 8px 24px rgba(58,44,35,0.08)" : "none";
      });
    }
  
    document.addEventListener("DOMContentLoaded", () => {
      renderShell();
      initInteractions();
    });
  
  })();