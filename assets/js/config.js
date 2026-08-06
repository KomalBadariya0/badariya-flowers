/* ==========================================================================
   CONFIG.JS — Badariya Flowers Website · Site Settings (FastAPI-backed)
   ----------------------------------------------------------------------
   SITE used to be a hardcoded object. It is now populated at runtime from
   the FastAPI backend's /api/settings endpoint (same admin Settings page
   at /admin/settings writes to this) — see assets/js/api.js for API_BASE
   / Api / mediaUrl. This file must load AFTER api.js.

   SITE keeps its old hardcoded values as fallback defaults, so the site
   still renders correctly even if the backend is offline or a field was
   never set in the admin panel — only fields actually returned by the
   API overwrite the defaults below.

   Every other site script reads the global `SITE` object the exact same
   way it always did (SITE.brand, SITE.whatsappNumber, SITE.phone, …) —
   the object reference never changes, only its properties are updated in
   place once the API responds, so code that read SITE.xyz before this
   file existed keeps working unchanged.

   Every page that uses SITE for anything beyond the synchronous defaults
   (WhatsApp links, footer contact info, address, business hours, social
   links, …) should wait on SITE_READY (a Promise) the same way pages
   already wait on CATALOGUE_READY:
     Promise.all([CATALOGUE_READY, SITE_READY]).then(render);
   ========================================================================== */

const SITE = {
  brand: "Badariya Flowers",
  tagline: "Handcrafted Artificial Flowers For Every Celebration",
  whatsappNumber: "",
  logo: "/assets/images/logo/logo.png",
  favicon: "/assets/images/logo/logo.png",
  phone: "+91 96678 57709",
  email: "info@badariyaflowers.com",
  address: "",
  city: "",
  state: "",
  country: "",
  pincode: "",
  businessHours: "",
  footerCopyright: "",
  facebook: "#",
  instagram: "#",
  youtube: "#",
  twitter: "#",
  pinterest: "#"
};

const SITE_READY = (async function loadSiteSettings(){
  try{
    const s = await Api.get("/settings");
    if(!s) return;
    Object.assign(SITE, {
      brand: s.websiteName || SITE.brand,
      tagline: s.tagline || SITE.tagline,
      whatsappNumber: s.whatsappNumber || SITE.whatsappNumber,
      logo: mediaUrl(s.logo) || SITE.logo,
      favicon: mediaUrl(s.favicon) || SITE.favicon,
      phone: s.mobileNumber || SITE.phone,
      email: s.businessEmail || SITE.email,
      address: [s.address, s.city, s.state, s.country, s.pincode].filter(Boolean).join(", "),
      city: s.city || "",
      state: s.state || "",
      country: s.country || "",
      pincode: s.pincode || "",
      businessHours: s.businessHours || "",
      footerCopyright: s.footerCopyright || "",
      facebook: s.facebook || SITE.facebook,
      instagram: s.instagram || SITE.instagram,
      youtube: s.youtube || SITE.youtube,
      twitter: s.twitter || SITE.twitter,
      pinterest: s.pinterest || SITE.pinterest
    });
    let iconLink = document.querySelector("link[rel~='icon']");
    if (!iconLink) {
      iconLink = document.createElement("link");
      iconLink.rel = "icon";
      document.head.appendChild(iconLink);
    }
    iconLink.href = SITE.favicon;
  }catch(err){
    console.error("Could not load site settings from the backend, using defaults:", err.message);
  }
})();
