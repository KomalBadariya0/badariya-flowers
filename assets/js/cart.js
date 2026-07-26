/* ==========================================================================
   CART ENGINE — localStorage-backed, key = "subId:no"
   ========================================================================== */
const CART_KEY = "badariya_cart_v1";

function cartRead(){
  try{
    const raw = localStorage.getItem(CART_KEY);
    return raw ? JSON.parse(raw) : {};
  }catch(e){ return {}; }
}
function cartWrite(cart){
  try{ localStorage.setItem(CART_KEY, JSON.stringify(cart)); }catch(e){ /* storage unavailable */ }
  document.dispatchEvent(new CustomEvent("cart:changed"));
}

function cartAdd(subId, no, qty){
  const cart = cartRead();
  const key = `${subId}:${no}`;
  const p = getProduct(subId, no);
  const startQty = qty != null ? qty : (p ? p.moq : 1);
  cart[key] = { subId, no, qty: (cart[key] ? cart[key].qty : 0) + startQty };
  cartWrite(cart);
  return cart[key].qty;
}
function cartSetQty(key, qty){
  const cart = cartRead();
  if(!cart[key]) return;
  if(qty <= 0){ delete cart[key]; }
  else{ cart[key].qty = qty; }
  cartWrite(cart);
}
function cartRemove(key){
  const cart = cartRead();
  delete cart[key];
  cartWrite(cart);
}
function cartClear(){ cartWrite({}); }

function cartItems(){
  const cart = cartRead();
  return Object.keys(cart).map(key => {
    const entry = cart[key];
    const p = getProduct(entry.subId, entry.no);
    if(!p) return null;
    return { key, qty: entry.qty, product: p, lineTotal: p.price != null ? p.price * entry.qty : null };
  }).filter(Boolean);
}
function cartCount(){
  const cart = cartRead();
  return Object.values(cart).reduce((n, e) => n + e.qty, 0);
}
function cartTotal(){
  return cartItems().reduce((sum, item) => sum + (item.lineTotal || 0), 0);
}
function cartHasPriceOnRequestItems(){
  return cartItems().some(item => item.product.price == null);
}

/* Update every [data-cart-badge] element on the page */
function refreshCartBadges(){
  const count = cartCount();
  document.querySelectorAll("[data-cart-badge]").forEach(el => {
    el.textContent = count;
    el.style.display = count > 0 ? "flex" : "none";
  });
}
document.addEventListener("cart:changed", refreshCartBadges);
document.addEventListener("DOMContentLoaded", refreshCartBadges);
