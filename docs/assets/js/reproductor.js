/* Reproduce un partido grabado (docs/replays/*.json). */

(function () {
  "use strict";

  var ESPERAS = [1600, 1000, 650, 400, 200, 70];
  var relato = document.getElementById("relato");
  var marcador = document.getElementById("marcador");
  var velocidad = document.getElementById("velocidad");
  var detalles = document.getElementById("detalles");

  var partido = null;
  var indice = 0;
  var temporizador = null;

  function visibles() {
    if (!partido) return [];
    return detalles.checked
      ? partido.eventos
      : partido.eventos.filter(function (ev) { return ev.nivel === "clave"; });
  }

  function paso() {
    var eventos = visibles();
    if (indice >= eventos.length) return false;
    var evento = eventos[indice];
    var anterior = relato.querySelector(".actual");
    if (anterior) anterior.classList.remove("actual");
    var linea = document.createElement("li");
    linea.className = evento.nivel + " " + evento.tipo + " actual";
    linea.textContent = evento.texto;
    relato.appendChild(linea);
    relato.scrollTop = relato.scrollHeight;
    marcador.textContent = evento.marcador[0] + " – " + evento.marcador[1];
    indice += 1;
    return true;
  }

  function reproducir() {
    if (!paso()) return;
    temporizador = setTimeout(reproducir, ESPERAS[parseInt(velocidad.value, 10) - 1]);
  }

  function pausar() {
    clearTimeout(temporizador);
    temporizador = null;
  }

  function reiniciar() {
    pausar();
    indice = 0;
    relato.innerHTML = "";
    marcador.textContent = "0 – 0";
  }

  document.getElementById("reproducir").onclick = function () { pausar(); reproducir(); };
  document.getElementById("pausar").onclick = pausar;
  document.getElementById("siguiente").onclick = function () { pausar(); paso(); };
  document.getElementById("reiniciar").onclick = reiniciar;
  detalles.onchange = reiniciar;

  fetch("replays/partido.json")
    .then(function (respuesta) {
      if (!respuesta.ok) throw new Error("no se pudo leer el partido grabado");
      return respuesta.json();
    })
    .then(function (datos) {
      partido = datos;
      document.getElementById("equipos").textContent =
        datos.equipos[0].join(", ") + "  vs  " + datos.equipos[1].join(", ");
      document.getElementById("ficha").textContent =
        "Reglamento " + datos.reglamento.id + " · " + datos.formato +
        " · semilla " + datos.semilla + " · " + datos.turnos + " turnos" +
        (datos.definido_por_penales ? " · definido por penales" : "");
      reproducir();
    })
    .catch(function (error) {
      relato.innerHTML = "";
      var linea = document.createElement("li");
      linea.textContent = "No se pudo cargar el partido: " + error.message;
      relato.appendChild(linea);
    });
})();
