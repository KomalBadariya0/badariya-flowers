/* ==========================================================================
   SLIDER.JS — pointer drag-scroll for horizontal category/product rows
   Only engages as a "drag" past a small movement threshold, so a normal
   tap/click on a card link still navigates normally.
   ========================================================================== */

(function(){
  const DRAG_THRESHOLD = 6; // px of movement before we treat this as a drag, not a click

  function enableDragScroll(el){
    let isDown = false, isDragging = false, startX, scrollLeft;

    el.addEventListener("pointerdown", (e) => {
      // Only left-click / primary touch, and don't hijack interactive elements immediately
      isDown = true;
      isDragging = false;
      startX = e.clientX;
      scrollLeft = el.scrollLeft;
    });

    el.addEventListener("pointermove", (e) => {
      if(!isDown) return;
      const dx = e.clientX - startX;
      if(Math.abs(dx) > DRAG_THRESHOLD){
        if(!isDragging){
          isDragging = true;
          el.setPointerCapture(e.pointerId);
          el.classList.add("is-dragging");
        }
        el.scrollLeft = scrollLeft - dx;
      }
    });

    // If a real drag happened, swallow the click that follows so links don't fire.
    el.addEventListener("click", (e) => {
      if(isDragging){
        e.preventDefault();
        e.stopPropagation();
      }
    }, true);

    ["pointerup","pointerleave","pointercancel"].forEach(evt =>
      el.addEventListener(evt, () => {
        isDown = false;
        el.classList.remove("is-dragging");
        // isDragging is reset after the click listener above has had a chance to check it
        setTimeout(() => { isDragging = false; }, 0);
      })
    );
  }

  document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll(".cat-scroller, .scroller-row").forEach(enableDragScroll);
  });
})();
