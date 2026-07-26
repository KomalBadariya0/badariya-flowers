/* ==========================================================================
   SETTINGS.JS — Badariya Flowers Admin · Settings Module
   ----------------------------------------------------------------------
   Written to be swapped onto a real backend with minimal changes:
     GET  /api/settings           -> SettingsAPI.get()
     PUT  /api/settings           -> SettingsAPI.update(payload)
     POST /api/logo               -> SettingsAPI.uploadLogo(file)
     POST /api/favicon            -> SettingsAPI.uploadFavicon(file)
     POST /api/settings/image     -> SettingsAPI.uploadDefaultProductImage(file)
     PUT  /api/settings/password  -> (wired later, see Security tab handler)

   Every SettingsAPI method already returns a Promise and already matches
   the shape a fetch() call would return, so the tab / form / upload code
   below never needs to change when the dummy layer is replaced.

   SINGLE SOURCE OF TRUTH
   There is exactly ONE settings record (not a list, unlike Categories /
   Products). Once FastAPI + MySQL land this becomes a single `settings`
   row (or key/value table) that both the admin panel AND the customer
   website read from — the website should fetch GET /api/settings on load
   and use it for site name, logo, favicon, footer contact info, social
   links and the WhatsApp number instead of any hardcoded copy, so nothing
   is ever duplicated between admin and the public site. This file is
   written so that swap is a pure data-layer change — no UI code changes
   required — and is exposed on window.SettingsAPI (same convention as
   window.ProductAPI in product_store.js) so a future website script can
   read it directly.
   ========================================================================== */

   (function(){

    /* ============================================================
       DUMMY DATA LAYER
       Stands in for MySQL until FastAPI is wired up. Persisted to
       localStorage only so the demo survives a page refresh — replace
       this whole block with real fetch() calls later. UI code above
       never touches localStorage directly, only SettingsAPI.
       ============================================================ */
    const STORAGE_KEY = "bf_admin_settings_v1";
  
    function delay(ms){ return new Promise(res => setTimeout(res, ms)); }
  
    function defaultSettings(){
      return {
        // General
        websiteName: "Badariya Flowers",
        logo: null,
        favicon: null,
        websiteStatus: "active",
        maintenanceMode: false,
  
        // Business Information
        businessName: "Badariya Flowers",
        ownerName: "",
        mobileNumber: "",
        whatsappNumber: "",
        businessEmail: "",
        mapLink: "",
        address: "",
  
        // Website Settings
        currency: "INR",
        language: "en",
        defaultProductImage: null,
        productsPerPage: 12,
        defaultWaMessage: "Hello Badariya Flowers, I'd like to know more about your products.",
  
        // Social Links
        facebook: "",
        instagram: "",
        youtube: "",
        pinterest: "",
        linkedin: "",
  
        // Footer
        footerCopyright: "© 2026 Badariya Flowers. All Rights Reserved.",
        footerAddress: "",
        footerPhone: "",
        footerEmail: "",
        footerWhatsapp: "",
  
        // Security (profile only — password is never persisted here)
        adminName: "Badariya Admin",
        adminEmail: "admin@badariyaflowers.com"
      };
    }
  
    function loadStore(){
      try{
        const raw = localStorage.getItem(STORAGE_KEY);
        if(raw) return { ...defaultSettings(), ...JSON.parse(raw) };
      }catch(e){ /* fall through to seed */ }
      const seeded = defaultSettings();
      saveStore(seeded);
      return seeded;
    }
    function saveStore(settings){ localStorage.setItem(STORAGE_KEY, JSON.stringify(settings)); }
  
    function readFileAsDataURL(file){
      return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => resolve(reader.result);
        reader.onerror = () => reject(new Error("Could not read image"));
        reader.readAsDataURL(file);
      });
    }
  
    const SettingsAPI = {
      async get(){
        // Future: GET /api/settings
        await delay(220);
        return { ...loadStore() };
      },
  
      async update(payload){
        // Future: PUT /api/settings
        await delay(320);
        const merged = { ...loadStore(), ...payload };
        saveStore(merged);
        return { ...merged };
      },
  
      async uploadLogo(file){
        // Future: POST /api/logo (multipart) -> { url }
        const url = await readFileAsDataURL(file);
        return { url };
      },
  
      async uploadFavicon(file){
        // Future: POST /api/favicon (multipart) -> { url }
        const url = await readFileAsDataURL(file);
        return { url };
      },
  
      async uploadDefaultProductImage(file){
        // Future: POST /api/settings/image (multipart) -> { url }
        const url = await readFileAsDataURL(file);
        return { url };
      }
    };
  
    window.SettingsAPI = SettingsAPI;
  
    /* ============================================================
       FIELD REGISTRY — drives validation + tab-jump on error.
       Every text/select/textarea field that needs validation is
       listed once here; plain fields (currency, language, textareas
       with no rules, toggles) are read directly in collectFormData().
       ============================================================ */
    const FIELDS = {
      websiteName:    { input: "settingsWebsiteName",    error: "settingsWebsiteNameError",    tab: "general",  required: true },
  
      businessName:   { input: "settingsBusinessName",   error: "settingsBusinessNameError",   tab: "business", required: true },
      ownerName:      { input: "settingsOwnerName",      error: "settingsOwnerNameError",      tab: "business", required: true },
      mobileNumber:   { input: "settingsMobileNumber",   error: "settingsMobileNumberError",   tab: "business", required: true, type: "phone" },
      whatsappNumber: { input: "settingsWhatsappNumber", error: "settingsWhatsappNumberError", tab: "business", required: true, type: "phone" },
      businessEmail:  { input: "settingsBusinessEmail",  error: "settingsBusinessEmailError",  tab: "business", required: true, type: "email" },
      mapLink:        { input: "settingsMapLink",        error: "settingsMapLinkError",        tab: "business", type: "url" },
  
      productsPerPage:{ input: "settingsProductsPerPage",error: "settingsProductsPerPageError",tab: "website",  type: "number", min: 4, max: 96 },
  
      facebook:       { input: "settingsFacebook",       error: "settingsFacebookError",       tab: "social",   type: "url" },
      instagram:      { input: "settingsInstagram",      error: "settingsInstagramError",      tab: "social",   type: "url" },
      youtube:        { input: "settingsYoutube",        error: "settingsYoutubeError",        tab: "social",   type: "url" },
      pinterest:      { input: "settingsPinterest",      error: "settingsPinterestError",      tab: "social",   type: "url" },
      linkedin:       { input: "settingsLinkedin",        error: "settingsLinkedinError",       tab: "social",   type: "url" },
  
      footerPhone:    { input: "settingsFooterPhone",    error: "settingsFooterPhoneError",    tab: "footer",   type: "phone" },
      footerEmail:    { input: "settingsFooterEmail",    error: "settingsFooterEmailError",    tab: "footer",   type: "email" },
      footerWhatsapp: { input: "settingsFooterWhatsapp", error: "settingsFooterWhatsappError",  tab: "footer",   type: "phone" },
  
      adminName:      { input: "settingsAdminName",      error: "settingsAdminNameError",      tab: "security", required: true },
      adminEmail:     { input: "settingsAdminEmail",      error: "settingsAdminEmailError",     tab: "security", required: true, type: "email" }
    };
  
    const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    const PHONE_RE = /^[+]?[\d\s-]{7,15}$/;
    const URL_RE = /^https?:\/\/[^\s]+\.[^\s]+/i;
  
    /* ============================================================
       DOM REFS
       ============================================================ */
    const form = document.getElementById("settingsForm");
    const tabsBar = document.getElementById("settingsTabs");
    const panels = document.querySelectorAll(".set-panel");
  
    const toast = document.getElementById("settingsToast");
    const toastMsg = document.getElementById("settingsToastMsg");
  
    const saveBtn = document.getElementById("settingsSaveBtn");
    const resetBtn = document.getElementById("settingsResetBtn");
    const cancelBtn = document.getElementById("settingsCancelBtn");
  
    const maintenanceToggle = document.getElementById("settingsMaintenanceMode");
    const maintenanceLabel = document.getElementById("settingsMaintenanceModeLabel");
  
    const footerSocialPreview = document.getElementById("footerSocialPreview");
  
    const passwordUpdateBtn = document.getElementById("settingsPasswordUpdateBtn");
    const currentPasswordInput = document.getElementById("settingsCurrentPassword");
    const newPasswordInput = document.getElementById("settingsNewPassword");
    const confirmPasswordInput = document.getElementById("settingsConfirmPassword");
  
    // in-memory only — never written to the settings payload
    const imageState = { logo: null, favicon: null, defaultProductImage: null };
    const defaultPreviewHTML = {};
  
    let lastSavedSnapshot = null; // for Cancel — discard unsaved changes
    let activeTab = "general";
  
    /* ============================================================
       TOAST
       ============================================================ */
    function showToast(message, type = "success"){
      toastMsg.textContent = message;
      toast.classList.remove("is-error", "is-success");
      toast.classList.add(type === "error" ? "is-error" : "is-success");
      toast.classList.add("is-open");
      clearTimeout(showToast._t);
      showToast._t = setTimeout(() => toast.classList.remove("is-open"), 2800);
    }
  
    /* ============================================================
       TABS
       ============================================================ */
    function switchTab(tabKey){
      activeTab = tabKey;
      tabsBar.querySelectorAll(".set-tab").forEach(btn => {
        const isActive = btn.dataset.tab === tabKey;
        btn.classList.toggle("is-active", isActive);
        btn.setAttribute("aria-selected", isActive ? "true" : "false");
      });
      panels.forEach(panel => {
        const isActive = panel.id === `panel-${tabKey}`;
        panel.hidden = !isActive;
        panel.classList.toggle("is-active", isActive);
      });
      if(tabKey === "footer") renderFooterSocialPreview();
    }
  
    tabsBar.addEventListener("click", (e) => {
      const btn = e.target.closest(".set-tab");
      if(!btn) return;
      switchTab(btn.dataset.tab);
    });
  
    document.querySelectorAll("[data-jump-tab]").forEach(btn => {
      btn.addEventListener("click", () => switchTab(btn.dataset.jumpTab));
    });
  
    // Optional deep link, e.g. settings.html#social
    const hashTab = (location.hash || "").replace("#", "");
    if(FIELDS_TAB_EXISTS(hashTab)) activeTab = hashTab;
    function FIELDS_TAB_EXISTS(key){
      return !!document.getElementById(`panel-${key}`);
    }
  
    /* ============================================================
       FIELD ERRORS
       ============================================================ */
    function clearAllFieldErrors(){
      Object.values(FIELDS).forEach(f => {
        const input = document.getElementById(f.input);
        const errorEl = document.getElementById(f.error);
        if(input) input.classList.remove("is-invalid");
        if(errorEl) errorEl.textContent = "";
      });
      ["logo", "favicon", "defaultProductImage"].forEach(key => {
        const el = document.getElementById(`${key}Error`);
        if(el) el.textContent = "";
      });
    }
  
    function setFieldError(fieldKey, message){
      const f = FIELDS[fieldKey];
      if(!f) return;
      const input = document.getElementById(f.input);
      const errorEl = document.getElementById(f.error);
      if(input) input.classList.add("is-invalid");
      if(errorEl) errorEl.textContent = message;
    }
  
    /* ============================================================
       VALIDATION
       ============================================================ */
    function validateForm(){
      clearAllFieldErrors();
      let firstErrorTab = null;
  
      Object.keys(FIELDS).forEach(key => {
        const f = FIELDS[key];
        const input = document.getElementById(f.input);
        if(!input) return;
        const raw = input.value.trim();
  
        let error = "";
        if(f.required && !raw){
          error = "This field is required";
        } else if(raw && f.type === "email" && !EMAIL_RE.test(raw)){
          error = "Enter a valid email address";
        } else if(raw && f.type === "phone" && !PHONE_RE.test(raw)){
          error = "Enter a valid phone number";
        } else if(raw && f.type === "url" && !URL_RE.test(raw)){
          error = "Enter a valid URL starting with http:// or https://";
        } else if(f.type === "number" && raw){
          const num = Number(raw);
          if(Number.isNaN(num) || num < f.min || num > f.max){
            error = `Enter a number between ${f.min} and ${f.max}`;
          }
        }
  
        if(error){
          setFieldError(key, error);
          if(!firstErrorTab) firstErrorTab = f.tab;
        }
      });
  
      return { valid: !firstErrorTab, firstErrorTab };
    }
  
    /* ============================================================
       IMAGE UPLOAD (mirrors categories.js / sub-categories.js pattern)
       ============================================================ */
    function setupImageUpload({ dropId, inputId, previewId, removeBtnId, errorId, maxBytes, sizeLabel, accept, stateKey, apiUploadFn }){
      const drop = document.getElementById(dropId);
      const input = document.getElementById(inputId);
      const preview = document.getElementById(previewId);
      const removeBtn = document.getElementById(removeBtnId);
      const errorEl = document.getElementById(errorId);
  
      defaultPreviewHTML[stateKey] = preview.innerHTML;
  
      drop.addEventListener("click", (e) => {
        if(e.target === removeBtn || removeBtn.contains(e.target)) return;
        input.click();
      });
  
      input.addEventListener("change", async () => {
        const file = input.files[0];
        if(!file) return;
        errorEl.textContent = "";
  
        if(!accept.includes(file.type) && !(stateKey === "favicon" && /\.ico$/i.test(file.name))){
          errorEl.textContent = "Unsupported file type";
          input.value = "";
          return;
        }
        if(file.size > maxBytes){
          errorEl.textContent = `Image must be under ${sizeLabel}`;
          input.value = "";
          return;
        }
  
        try{
          const { url } = await apiUploadFn(file);
          imageState[stateKey] = url;
          preview.innerHTML = `<img src="${url}" alt="">`;
          removeBtn.hidden = false;
        }catch(err){
          errorEl.textContent = err.message || "Could not read image";
        }
      });
  
      removeBtn.addEventListener("click", (e) => {
        e.stopPropagation();
        imageState[stateKey] = null;
        preview.innerHTML = defaultPreviewHTML[stateKey];
        removeBtn.hidden = true;
        input.value = "";
      });
    }
  
    setupImageUpload({
      dropId: "logoDrop", inputId: "logoInput", previewId: "logoPreview", removeBtnId: "logoRemoveBtn",
      errorId: "logoError", maxBytes: 2 * 1024 * 1024, sizeLabel: "2MB",
      accept: ["image/png", "image/jpeg"], stateKey: "logo", apiUploadFn: SettingsAPI.uploadLogo
    });
    setupImageUpload({
      dropId: "faviconDrop", inputId: "faviconInput", previewId: "faviconPreview", removeBtnId: "faviconRemoveBtn",
      errorId: "faviconError", maxBytes: 512 * 1024, sizeLabel: "512KB",
      accept: ["image/png", "image/x-icon", "image/vnd.microsoft.icon"], stateKey: "favicon", apiUploadFn: SettingsAPI.uploadFavicon
    });
    setupImageUpload({
      dropId: "defaultProductImageDrop", inputId: "defaultProductImageInput", previewId: "defaultProductImagePreview",
      removeBtnId: "defaultProductImageRemoveBtn", errorId: "defaultProductImageError", maxBytes: 2 * 1024 * 1024,
      sizeLabel: "2MB", accept: ["image/png", "image/jpeg"], stateKey: "defaultProductImage", apiUploadFn: SettingsAPI.uploadDefaultProductImage
    });
  
    /* ============================================================
       MAINTENANCE MODE TOGGLE
       ============================================================ */
    maintenanceToggle.addEventListener("change", () => {
      maintenanceLabel.textContent = maintenanceToggle.checked ? "On" : "Off";
    });
  
    /* ============================================================
       FOOTER SOCIAL PREVIEW (read-only mirror of the Social tab —
       never a second copy of the data, just re-reads those inputs)
       ============================================================ */
    const SOCIAL_PLATFORMS = [
      { key: "facebook",  label: "Facebook" },
      { key: "instagram", label: "Instagram" },
      { key: "youtube",   label: "YouTube" },
      { key: "pinterest", label: "Pinterest" },
      { key: "linkedin",  label: "LinkedIn" }
    ];
  
    function renderFooterSocialPreview(){
      const active = SOCIAL_PLATFORMS.filter(p => {
        const el = document.getElementById(FIELDS[p.key].input);
        return el && el.value.trim();
      });
  
      if(!active.length){
        footerSocialPreview.innerHTML = `<span class="set-footer-social-chip is-empty">No social links added yet</span>`;
        return;
      }
  
      footerSocialPreview.innerHTML = active.map(p => `<span class="set-footer-social-chip">${p.label}</span>`).join("");
    }
  
    ["facebook", "instagram", "youtube", "pinterest", "linkedin"].forEach(key => {
      document.getElementById(FIELDS[key].input).addEventListener("input", renderFooterSocialPreview);
    });
  
    /* ============================================================
       FORM <-> DATA
       ============================================================ */
    function populateForm(settings){
      document.getElementById("settingsWebsiteName").value = settings.websiteName || "";
      document.getElementById("settingsWebsiteStatus").value = settings.websiteStatus || "active";
      maintenanceToggle.checked = !!settings.maintenanceMode;
      maintenanceLabel.textContent = maintenanceToggle.checked ? "On" : "Off";
  
      document.getElementById("settingsBusinessName").value = settings.businessName || "";
      document.getElementById("settingsOwnerName").value = settings.ownerName || "";
      document.getElementById("settingsMobileNumber").value = settings.mobileNumber || "";
      document.getElementById("settingsWhatsappNumber").value = settings.whatsappNumber || "";
      document.getElementById("settingsBusinessEmail").value = settings.businessEmail || "";
      document.getElementById("settingsMapLink").value = settings.mapLink || "";
      document.getElementById("settingsAddress").value = settings.address || "";
  
      document.getElementById("settingsCurrency").value = settings.currency || "INR";
      document.getElementById("settingsLanguage").value = settings.language || "en";
      document.getElementById("settingsProductsPerPage").value = settings.productsPerPage || 12;
      document.getElementById("settingsDefaultWaMessage").value = settings.defaultWaMessage || "";
  
      document.getElementById("settingsFacebook").value = settings.facebook || "";
      document.getElementById("settingsInstagram").value = settings.instagram || "";
      document.getElementById("settingsYoutube").value = settings.youtube || "";
      document.getElementById("settingsPinterest").value = settings.pinterest || "";
      document.getElementById("settingsLinkedin").value = settings.linkedin || "";
  
      document.getElementById("settingsFooterCopyright").value = settings.footerCopyright || "";
      document.getElementById("settingsFooterAddress").value = settings.footerAddress || "";
      document.getElementById("settingsFooterPhone").value = settings.footerPhone || "";
      document.getElementById("settingsFooterEmail").value = settings.footerEmail || "";
      document.getElementById("settingsFooterWhatsapp").value = settings.footerWhatsapp || "";
  
      document.getElementById("settingsAdminName").value = settings.adminName || "";
      document.getElementById("settingsAdminEmail").value = settings.adminEmail || "";
  
      // Images
      [["logo", "logoPreview", "logoRemoveBtn"],
       ["favicon", "faviconPreview", "faviconRemoveBtn"],
       ["defaultProductImage", "defaultProductImagePreview", "defaultProductImageRemoveBtn"]
      ].forEach(([key, previewId, removeBtnId]) => {
        const preview = document.getElementById(previewId);
        const removeBtn = document.getElementById(removeBtnId);
        imageState[key] = settings[key] || null;
        if(settings[key]){
          preview.innerHTML = `<img src="${settings[key]}" alt="">`;
          removeBtn.hidden = false;
        } else {
          preview.innerHTML = defaultPreviewHTML[key] || preview.innerHTML;
          removeBtn.hidden = true;
        }
      });
  
      renderFooterSocialPreview();
    }
  
    function collectFormData(){
      return {
        websiteName: document.getElementById("settingsWebsiteName").value.trim(),
        websiteStatus: document.getElementById("settingsWebsiteStatus").value,
        maintenanceMode: maintenanceToggle.checked,
        logo: imageState.logo,
        favicon: imageState.favicon,
  
        businessName: document.getElementById("settingsBusinessName").value.trim(),
        ownerName: document.getElementById("settingsOwnerName").value.trim(),
        mobileNumber: document.getElementById("settingsMobileNumber").value.trim(),
        whatsappNumber: document.getElementById("settingsWhatsappNumber").value.trim(),
        businessEmail: document.getElementById("settingsBusinessEmail").value.trim(),
        mapLink: document.getElementById("settingsMapLink").value.trim(),
        address: document.getElementById("settingsAddress").value.trim(),
  
        currency: document.getElementById("settingsCurrency").value,
        language: document.getElementById("settingsLanguage").value,
        defaultProductImage: imageState.defaultProductImage,
        productsPerPage: Number(document.getElementById("settingsProductsPerPage").value) || 12,
        defaultWaMessage: document.getElementById("settingsDefaultWaMessage").value.trim(),
  
        facebook: document.getElementById("settingsFacebook").value.trim(),
        instagram: document.getElementById("settingsInstagram").value.trim(),
        youtube: document.getElementById("settingsYoutube").value.trim(),
        pinterest: document.getElementById("settingsPinterest").value.trim(),
        linkedin: document.getElementById("settingsLinkedin").value.trim(),
  
        footerCopyright: document.getElementById("settingsFooterCopyright").value.trim(),
        footerAddress: document.getElementById("settingsFooterAddress").value.trim(),
        footerPhone: document.getElementById("settingsFooterPhone").value.trim(),
        footerEmail: document.getElementById("settingsFooterEmail").value.trim(),
        footerWhatsapp: document.getElementById("settingsFooterWhatsapp").value.trim(),
  
        adminName: document.getElementById("settingsAdminName").value.trim(),
        adminEmail: document.getElementById("settingsAdminEmail").value.trim()
      };
    }
  
    /* ============================================================
       SAVE / RESET / CANCEL
       ============================================================ */
    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      const { valid, firstErrorTab } = validateForm();
      if(!valid){
        switchTab(firstErrorTab);
        showToast("Please fix the highlighted fields", "error");
        return;
      }
  
      const payload = collectFormData();
      saveBtn.disabled = true;
      const originalLabel = saveBtn.textContent;
      saveBtn.textContent = "Saving…";
  
      try{
        const saved = await SettingsAPI.update(payload);
        lastSavedSnapshot = saved;
        showToast("Settings saved successfully");
      }catch(err){
        showToast(err.message || "Could not save settings", "error");
      }finally{
        saveBtn.disabled = false;
        saveBtn.textContent = originalLabel;
      }
    });
  
    resetBtn.addEventListener("click", () => {
      const ok = window.confirm("Reset all fields to their default values? This won't be saved until you click Save Settings.");
      if(!ok) return;
      populateForm(defaultSettings());
      clearAllFieldErrors();
      showToast("Fields reset to defaults — click Save Settings to apply");
    });
  
    cancelBtn.addEventListener("click", () => {
      if(lastSavedSnapshot){
        populateForm(lastSavedSnapshot);
        clearAllFieldErrors();
        showToast("Unsaved changes discarded");
      }
    });
  
    /* ============================================================
       SECURITY TAB — Change Password (UI only, no backend yet)
       ============================================================ */
    passwordUpdateBtn.addEventListener("click", () => {
      [currentPasswordInput, newPasswordInput, confirmPasswordInput].forEach(el => el.classList.remove("is-invalid"));
      ["settingsCurrentPasswordError", "settingsNewPasswordError", "settingsConfirmPasswordError"].forEach(id => {
        document.getElementById(id).textContent = "";
      });
  
      const current = currentPasswordInput.value;
      const next = newPasswordInput.value;
      const confirm = confirmPasswordInput.value;
      let hasError = false;
  
      if(!current){
        document.getElementById("settingsCurrentPasswordError").textContent = "Enter your current password";
        currentPasswordInput.classList.add("is-invalid");
        hasError = true;
      }
      if(!next || next.length < 6){
        document.getElementById("settingsNewPasswordError").textContent = "New password must be at least 6 characters";
        newPasswordInput.classList.add("is-invalid");
        hasError = true;
      }
      if(confirm !== next || !confirm){
        document.getElementById("settingsConfirmPasswordError").textContent = "Passwords do not match";
        confirmPasswordInput.classList.add("is-invalid");
        hasError = true;
      }
  
      if(hasError){
        showToast("Please fix the password fields", "error");
        return;
      }
  
      // Future: PUT /api/settings/password  { currentPassword, newPassword }
      showToast("Password update is UI only — connect PUT /api/settings/password later");
      currentPasswordInput.value = "";
      newPasswordInput.value = "";
      confirmPasswordInput.value = "";
    });
  
    /* ============================================================
       INIT
       ============================================================ */
    async function init(){
      switchTab(activeTab);
      try{
        const settings = await SettingsAPI.get();
        lastSavedSnapshot = settings;
        populateForm(settings);
      }catch(err){
        showToast("Could not load settings", "error");
      }
    }
  
    init();
  
  })();