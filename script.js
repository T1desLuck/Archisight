// Archisight — минимальная логика сайта: мобильное меню,
// плавное появление блоков при прокрутке, активный пункт
// оглавления на странице документации.

(function () {
  "use strict";

  // Мобильное меню
  var toggle = document.getElementById("nav-toggle");
  var nav = document.getElementById("main-nav");
  if (toggle && nav) {
    toggle.addEventListener("click", function () {
      var isOpen = nav.classList.toggle("is-open");
      toggle.setAttribute("aria-expanded", isOpen ? "true" : "false");
    });
    nav.querySelectorAll("a").forEach(function (link) {
      link.addEventListener("click", function () {
        nav.classList.remove("is-open");
        toggle.setAttribute("aria-expanded", "false");
      });
    });
  }

  // Появление элементов при прокрутке
  var revealEls = document.querySelectorAll(".reveal");
  if ("IntersectionObserver" in window && revealEls.length) {
    var io = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            entry.target.classList.add("is-visible");
            io.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.12 }
    );
    revealEls.forEach(function (el) {
      io.observe(el);
    });
  } else {
    revealEls.forEach(function (el) {
      el.classList.add("is-visible");
    });
  }

  // Подсветка текущего раздела в оглавлении документации
  var docsSections = document.querySelectorAll(".docs-section[id]");
  var docsLinks = document.querySelectorAll(".docs-nav a");
  if ("IntersectionObserver" in window && docsSections.length && docsLinks.length) {
    var sectionIO = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            docsLinks.forEach(function (link) {
              link.classList.toggle(
                "active",
                link.getAttribute("href") === "#" + entry.target.id
              );
            });
          }
        });
      },
      { rootMargin: "-20% 0px -70% 0px" }
    );
    docsSections.forEach(function (section) {
      sectionIO.observe(section);
    });
  }
})();
