/* Detalles compartidos por todas las páginas del sitio. */

// Marcar en qué página estamos.
(function () {
  "use strict";
  var pagina = location.pathname.split("/").pop() || "index.html";
  document.querySelectorAll("nav a[data-pagina]").forEach(function (enlace) {
    if (enlace.dataset.pagina === pagina) enlace.classList.add("activa");
  });

  if (!location.hostname.endsWith(".github.io")) return;

  var usuario = location.hostname.replace(".github.io", "");
  var repo = location.pathname.split("/").filter(Boolean)[0];
  if (!repo) return;
  var baseRepo = "https://github.com/" + usuario + "/" + repo;

  // El enlace del pie apunta al repositorio que sirve este sitio.
  var enlaceRepo = document.getElementById("enlace-repo");
  if (enlaceRepo) enlaceRepo.href = baseRepo;

  // GitHub Pages sirve los .md en crudo; GitHub los muestra formateados.
  document.querySelectorAll('a[href$=".md"]').forEach(function (enlace) {
    var archivo = enlace.getAttribute("href").replace(/^\.\//, "");
    enlace.href = baseRepo + "/blob/main/docs/" + archivo;
  });
})();
