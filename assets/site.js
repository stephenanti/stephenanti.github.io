(function () {
  var smooth = !(window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches);

  // "Back to top" and in-page menu links scroll without changing the address bar
  document.querySelectorAll(".js-top").forEach(function (a) {
    a.addEventListener("click", function (e) {
      e.preventDefault();
      window.scrollTo({ top: 0, behavior: smooth ? "smooth" : "auto" });
    });
  });
  document.querySelectorAll('nav.top .links a[href^="#"]').forEach(function (a) {
    a.addEventListener("click", function (e) {
      var t = document.getElementById(a.getAttribute("href").slice(1));
      if (!t) return;
      e.preventDefault();
      t.scrollIntoView({ behavior: smooth ? "smooth" : "auto" });
    });
  });
  if (location.hash === "#top" && history.replaceState) {
    history.replaceState(null, "", location.pathname + location.search);
  }

  // hide images that fail to load, leaving the title in the box
  document.querySelectorAll(".thumb img").forEach(function (im) {
    im.addEventListener("error", function () { im.hidden = true; });
  });
  var photo = document.getElementById("photo");
  if (photo) {
    photo.addEventListener("error", function () { photo.style.visibility = "hidden"; });
    if (photo.complete && photo.naturalWidth === 0) photo.style.visibility = "hidden";
  }

  // Work page: show one type of work at a time
  var buttons = document.querySelectorAll(".filters button");
  function show(id) {
    buttons.forEach(function (b) {
      var on = b.getAttribute("data-show") === id;
      b.classList.toggle("on", on);
      b.setAttribute("aria-pressed", on ? "true" : "false");
    });
    document.querySelectorAll(".work-group").forEach(function (g) {
      g.hidden = !(id === "all" || g.id === id);
    });
  }
  buttons.forEach(function (b) {
    b.addEventListener("click", function () { show(b.getAttribute("data-show")); });
  });
  if (buttons.length && location.hash) {
    var id = location.hash.slice(1);
    if (document.querySelector('.filters button[data-show="' + id + '"]')) show(id);
  }

  var yr = document.getElementById("yr");
  if (yr) yr.textContent = new Date().getFullYear();
})();
