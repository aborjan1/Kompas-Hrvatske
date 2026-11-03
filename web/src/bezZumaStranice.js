// The page itself never zooms from a pinch. On a phone a pinch on a panel zoomed the
// whole interface, with page scrollbars, instead of the map; pinches belong to the map,
// which handles its own (Mapbox, src/map/odzumiravanje.js). Keyboard zoom (Ctrl + and −)
// stays, for anyone who needs larger text. Chrome and Firefox follow `touch-action` in
// app.css; this covers what they don't.
export function bezZumaStranice() {
  // Safari (iPhone, iPad) zooms the page with its own gesture events.
  for (const vrsta of ['gesturestart', 'gesturechange']) {
    document.addEventListener(vrsta, (e) => e.preventDefault(), { passive: false });
  }
  // A trackpad pinch reaches the browser as Ctrl + wheel; over a panel it would zoom the
  // page. Over the map Mapbox has already taken it.
  document.addEventListener('wheel', (e) => {
    if (e.ctrlKey) e.preventDefault();
  }, { passive: false });
}
