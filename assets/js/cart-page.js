/* ==========================================================================
   CART-PAGE.JS — controller for cart.html
   ========================================================================== */
(function(){

  function cartItemRowHTML(item){
    const p = item.product;
    return `
      <div class="cart-item" data-key="${item.key}">
        <img src="${p.imgSrc}" alt="${esc(p.name)}">
        <div class="cart-item-body">
          <div class="cart-item-name">${esc(p.name)}</div>
          <div class="cart-item-price">${p.priceLabel}${item.lineTotal != null ? ` × ${item.qty} = ₹${item.lineTotal}` : ""}</div>
          <div class="cart-item-controls">
            <div class="qty-stepper">
              <button type="button" data-qty-minus>−</button>
              <input type="text" inputmode="numeric" value="${item.qty}" data-qty-input readonly>
              <button type="button" data-qty-plus>+</button>
            </div>
            <button type="button" class="cart-item-remove" data-remove>Remove</button>
          </div>
        </div>
      </div>`;
  }

  function render(){
    const items = cartItems();
    const filledWrap = document.getElementById("cartFilled");
    const emptyWrap = document.getElementById("cartEmpty");
    const pageCount = document.getElementById("cartPageCount");

    if(!items.length){
      filledWrap.style.display = "none";
      emptyWrap.style.display = "block";
      if(pageCount) pageCount.textContent = "";
      return;
    }

    filledWrap.style.display = "block";
    emptyWrap.style.display = "none";

    const totalQty = items.reduce((n, i) => n + i.qty, 0);
    if(pageCount) pageCount.textContent = `${totalQty} item${totalQty === 1 ? "" : "s"}`;

    const hasPOR = cartHasPriceOnRequestItems();
    document.getElementById("cartTotalAmt").textContent = hasPOR
      ? `₹${cartTotal()}+`
      : `₹${cartTotal()}`;
    document.getElementById("cartTotalCnt").textContent = `${totalQty} item${totalQty === 1 ? "" : "s"}${hasPOR ? " · some prices on request" : ""}`;

    document.getElementById("cartItemsHeading").textContent = `Items (${items.length})`;
    document.getElementById("cartItemsList").innerHTML = items.map(cartItemRowHTML).join("");

    document.getElementById("cartItemsList").querySelectorAll(".cart-item").forEach(row => {
      const key = row.dataset.key;
      const item = items.find(i => i.key === key);
      row.querySelector("[data-qty-minus]").addEventListener("click", () => {
        cartSetQty(key, item.qty - 1);
      });
      row.querySelector("[data-qty-plus]").addEventListener("click", () => {
        cartSetQty(key, item.qty + 1);
      });
      row.querySelector("[data-remove]").addEventListener("click", () => {
        cartRemove(key);
        toast("Removed from cart");
      });
    });
  }

  function init(){
    document.getElementById("fabWa").innerHTML = ICONS.whatsapp;
    document.getElementById("fabWa").href = waGeneralLink();

    document.getElementById("breadcrumbRow").innerHTML = `
      <a href="/">Home</a> <span class="sep">/</span>
      <span class="current">Your Cart</span>`;

    const askBtn = document.getElementById("cartAskWaBtn");
    if(askBtn) askBtn.href = waGeneralLink();

    const confirmIcon = document.getElementById("cartConfirmIcon");
    if(confirmIcon) confirmIcon.innerHTML = ICONS.whatsapp;

    const confirmBtn = document.getElementById("cartConfirmBtn");
    if(confirmBtn){
      confirmBtn.addEventListener("click", () => {
        if(!cartItems().length){ toast("Your cart is empty"); return; }

        const nameInput = document.getElementById("cartCustomerName");
        const phoneInput = document.getElementById("cartCustomerPhone");
        const noteInput = document.getElementById("cartNote");

        const name = nameInput.value.trim();
        const phone = phoneInput.value.trim();

        if(!name){ nameInput.focus(); toast("Please enter your name"); return; }
        if(!phone){ phoneInput.focus(); toast("Please enter your phone number"); return; }

        const link = waOrderLink(name, phone, noteInput.value.trim());
        window.open(link, "_blank", "noopener");
        toast("Opening WhatsApp to confirm your order…");
      });
    }

    render();
    document.addEventListener("cart:changed", render);
  }

  document.addEventListener("DOMContentLoaded", () => { Promise.all([CATALOGUE_READY, SITE_READY]).then(init); });
})();
