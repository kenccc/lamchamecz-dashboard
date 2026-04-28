(function () {
  "use strict";

  function on(el, ev, fn) { el.addEventListener(ev, fn); }

  function initNav() {
    var toggle = document.querySelector("[data-nav-toggle]");
    var menu = document.querySelector("[data-nav-menu]");
    if (toggle && menu) {
      on(toggle, "click", function () {
        menu.classList.toggle("is-open");
      });
    }

    var path = window.location.pathname;
    document.querySelectorAll(".glass-nav__link").forEach(function (link) {
      var href = link.getAttribute("href");
      if (href && href !== "/" && path.indexOf(href) === 0) {
        link.classList.add("is-active");
      } else if (href === "/" && path === "/") {
        link.classList.add("is-active");
      }
    });
  }

  function initFlash() {
    document.querySelectorAll("[data-flash-close]").forEach(function (btn) {
      on(btn, "click", function () {
        var flash = btn.closest(".flash");
        if (!flash) return;
        flash.style.transition = "opacity 180ms, transform 180ms";
        flash.style.opacity = "0";
        flash.style.transform = "translateX(16px)";
        setTimeout(function () { flash.remove(); }, 200);
      });
    });
  }

  function initConfirm() {
    document.querySelectorAll("[data-confirm]").forEach(function (form) {
      on(form, "submit", function (e) {
        var msg = form.getAttribute("data-confirm") || "Opravdu?";
        if (!window.confirm(msg)) e.preventDefault();
      });
    });
  }

  function initReveal() {
    var nodes = document.querySelectorAll("[data-reveal]");
    if (!nodes.length) return;

    // Set per-element stagger index, capped at 12.
    var groups = {};
    nodes.forEach(function (el) {
      var group = el.getAttribute("data-reveal-group") || "_";
      groups[group] = groups[group] || 0;
      var i = groups[group]++;
      el.style.setProperty("--reveal-i", Math.min(i, 12));
    });

    if (!("IntersectionObserver" in window)) {
      nodes.forEach(function (el) { el.classList.add("is-visible"); });
      return;
    }

    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add("is-visible");
          io.unobserve(entry.target);
        }
      });
    }, { rootMargin: "0px 0px -8% 0px", threshold: 0.05 });

    nodes.forEach(function (el) { io.observe(el); });
  }

  document.addEventListener("DOMContentLoaded", function () {
    initNav();
    initFlash();
    initConfirm();
    initReveal();
  });
})();
