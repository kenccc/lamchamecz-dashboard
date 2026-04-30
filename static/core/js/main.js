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

  function initFormsetDelete() {
    document.getElementById("formset-body") && document.getElementById("formset-body").addEventListener("click", function (e) {
      var btn = e.target.closest("[data-delete-row]");
      if (!btn) return;
      var row = btn.closest("tr");
      if (!row) return;
      var deleteCheckbox = row.querySelector("input[type=checkbox]");
      if (deleteCheckbox) {
        deleteCheckbox.checked = true;
        row.style.opacity = "0.4";
        btn.disabled = true;
      } else {
        var tbody = row.parentElement;
        var prefix = document.querySelector("[data-formset-add]");
        var prefixName = prefix && prefix.getAttribute("data-prefix");
        var totalInput = prefixName && document.querySelector("[name=" + prefixName + "-TOTAL_FORMS]");
        row.remove();
        if (totalInput) totalInput.value = parseInt(totalInput.value, 10) - 1;
      }
    });
  }

  function initFormsetAdd() {
    document.querySelectorAll("[data-formset-add]").forEach(function (btn) {
      btn.addEventListener("click", function () {
        var prefix = btn.getAttribute("data-prefix");
        var templateId = btn.getAttribute("data-template-id");
        var tmpl = document.getElementById(templateId);
        var tbody = document.getElementById("formset-body");
        var totalInput = document.querySelector("[name=" + prefix + "-TOTAL_FORMS]");
        if (!tmpl || !tbody || !totalInput) return;

        var total = parseInt(totalInput.value, 10);
        var html = tmpl.innerHTML.replace(/__prefix__/g, total);
        var tmp = document.createElement("tbody");
        tmp.innerHTML = html;
        var row = tmp.firstElementChild;
        var numCell = row.querySelector(".formset-row-num");
        if (numCell) numCell.textContent = total + 1;
        tbody.appendChild(row);
        totalInput.value = total + 1;
      });
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    initNav();
    initFlash();
    initConfirm();
    initReveal();
    initFormsetAdd();
    initFormsetDelete();
  });
})();
