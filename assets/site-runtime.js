/**
 * Manifold of Failure — Newsprint runtime
 *
 * Minimal client-side helpers. We DO NOT inject DOM nodes into React's
 * managed tree (that triggers hydration error #418). All masthead,
 * byline, and colophon decoration is done via CSS pseudo-elements in
 * site-overrides.css.
 *
 * Responsibilities:
 *   1. Force light mode permanently (Newsprint is single-palette).
 *   2. Hide the deprecated "Attack-Style Centroids" card if it ever renders
 *      (defense in depth — the JS chunk is also patched).
 */
(function () {
  "use strict";

  if (typeof window === "undefined" || typeof document === "undefined") return;

  function forceLight() {
    try { localStorage.setItem("theme", "light"); } catch (_) {}
    var html = document.documentElement;
    if (html.classList.contains("dark")) html.classList.remove("dark");
    html.style.colorScheme = "light";
  }

  function watchTheme() {
    var html = document.documentElement;
    var mo = new MutationObserver(function () {
      if (html.classList.contains("dark")) html.classList.remove("dark");
    });
    mo.observe(html, { attributes: true, attributeFilter: ["class"] });
  }

  var REMOVED_TITLES = ["Attack-Style Centroids"];

  function hideRemovedCards(root) {
    var titles = root.querySelectorAll('[data-slot="card-title"]');
    for (var i = 0; i < titles.length; i++) {
      var t = titles[i];
      var text = (t.textContent || "").trim();
      if (REMOVED_TITLES.indexOf(text) === -1) continue;
      var card = t.closest('[data-slot="card"]');
      if (card && card.dataset.mofHide !== "attack-style-centroids") {
        // Setting a data-attribute on an existing React element does NOT
        // remove the node, so React's reconciler is unaffected.
        card.dataset.mofHide = "attack-style-centroids";
      }
    }
  }

  function init() {
    forceLight();
    watchTheme();
    hideRemovedCards(document);

    var mo = new MutationObserver(function (mutations) {
      for (var i = 0; i < mutations.length; i++) {
        var added = mutations[i].addedNodes;
        for (var j = 0; j < added.length; j++) {
          var node = added[j];
          if (node && node.nodeType === 1) hideRemovedCards(node);
        }
      }
    });
    mo.observe(document.body, { childList: true, subtree: true });
  }

  // Run forceLight at module load to avoid a flash before init.
  forceLight();

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init, { once: true });
  } else {
    init();
  }
})();
