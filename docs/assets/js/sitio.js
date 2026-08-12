/* Fobal Facu — sitio público.
   Tres cosas: la tabla del dado interactiva, el partido grabado y la navegación. */

(function () {
  "use strict";

  /* ── La tabla del dado (reglamento v1 y v2) ─────────────────────── */

  var TABLA = [
    { pases: 0, gol: [1, 1], ataja: [2, 6] },
    { pases: 1, gol: [1, 2], ataja: [3, 6] },
    { pases: 2, gol: [1, 3], ataja: [4, 6] },
    { pases: 3, gol: [1, 4], ataja: [5, 6] },
    { pases: 4, gol: [1, 5], ataja: [6, 6] },
  ];
  var REBOTE = true;
  var PALO = true;

  var PUNTOS = {
    1: [4], 2: [0, 8], 3: [0, 4, 8], 4: [0, 2, 6, 8],
    5: [0, 2, 4, 6, 8], 6: [0, 2, 3, 5, 6, 8],
  };

  function entra(valor, rango) { return valor >= rango[0] && valor <= rango[1]; }

  function resolver(franja, pateador, arquero) {
    var esGol = entra(pateador, franja.gol);
    var ataja = entra(arquero, franja.ataja);
    if (REBOTE && esGol && ataja) return "rebote";
    if (PALO && pateador === arquero) return "palo";
    return esGol && !ataja ? "gol" : "atajada";
  }

  /* Probabilidad de gol contando que rebote y palo obligan a repetir. */
  function probabilidadGol(franja) {
    var goles = 0, resuelven = 0;
    for (var p = 1; p <= 6; p++) {
      for (var a = 1; a <= 6; a++) {
        var r = resolver(franja, p, a);
        if (r === "rebote" || r === "palo") continue;
        resuelven++;
        if (r === "gol") goles++;
      }
    }
    return resuelven ? goles / resuelven : 0;
  }

  function pintarDado(elemento, valor) {
    elemento.innerHTML = "";
    var puntos = PUNTOS[valor] || [];
    for (var i = 0; i < 9; i++) {
      var celda = document.createElement("span");
      if (puntos.indexOf(i) !== -1) celda.appendChild(document.createElement("i"));
      elemento.appendChild(celda);
    }
    elemento.setAttribute("aria-label", "dado en " + valor);
  }

  function laboratorioDelDado() {
    var selector = document.getElementById("selector-pases");
    if (!selector) return;

    var cuerpoTabla = document.querySelector("#tabla-dado tbody");
    var dadoPateador = document.getElementById("dado-pateador");
    var dadoArquero = document.getElementById("dado-arquero");
    var resultado = document.getElementById("resultado-tiro");
    var conteo = document.getElementById("conteo-tiros");
    var elegida = 2;
    var tiros = { gol: 0, total: 0 };

    TABLA.forEach(function (franja, indice) {
      var boton = document.createElement("button");
      boton.type = "button";
      boton.textContent = franja.pases === 4 ? "4+" : String(franja.pases);
      boton.setAttribute("aria-pressed", String(indice === elegida));
      boton.onclick = function () { elegir(indice); };
      selector.appendChild(boton);

      var fila = document.createElement("tr");
      fila.innerHTML =
        "<td><strong>" + (franja.pases === 4 ? "4 o más" : franja.pases) + "</strong></td>" +
        "<td>" + caras(franja, "gol") + "</td>" +
        "<td>" + caras(franja, "ataja") + "</td>" +
        '<td class="prob" style="text-align:right">' +
        Math.round(probabilidadGol(franja) * 100) + " %</td>";
      cuerpoTabla.appendChild(fila);
    });

    function caras(franja, cual) {
      var salida = '<div class="caras">';
      for (var n = 1; n <= 6; n++) {
        var clase = entra(n, franja[cual]) ? (cual === "gol" ? "gol" : "ataja") : "";
        salida += '<span class="cara ' + clase + '">' + n + "</span>";
      }
      return salida + "</div>";
    }

    function elegir(indice) {
      elegida = indice;
      Array.prototype.forEach.call(selector.children, function (boton, i) {
        boton.setAttribute("aria-pressed", String(i === indice));
      });
      Array.prototype.forEach.call(cuerpoTabla.children, function (fila, i) {
        fila.classList.toggle("activa", i === indice);
      });
      tiros = { gol: 0, total: 0 };
      conteo.innerHTML = "&nbsp;";
      resultado.className = "resultado-tiro";
      resultado.textContent = "Tirá los dados";
    }

    var TEXTOS = {
      gol: "¡GOL!",
      atajada: "La ataja el arquero",
      rebote: "Rebote: se vuelve a patear",
      palo: "Al palo: se vuelve a patear",
    };

    function tirar(silencioso) {
      var franja = TABLA[elegida];
      var p = 1 + Math.floor(Math.random() * 6);
      var a = 1 + Math.floor(Math.random() * 6);
      pintarDado(dadoPateador, p);
      pintarDado(dadoArquero, a);
      var r = resolver(franja, p, a);
      resultado.className = "resultado-tiro " + (r === "gol" ? "gol" : r === "atajada" ? "atajada" : "repetir");
      resultado.textContent = TEXTOS[r];

      if (r !== "rebote" && r !== "palo") {
        tiros.total++;
        if (r === "gol") tiros.gol++;
      }
      if (tiros.total) {
        conteo.textContent = tiros.gol + " gol" + (tiros.gol === 1 ? "" : "es") +
          " en " + tiros.total + " remate" + (tiros.total === 1 ? "" : "s") + " que se resolvieron";
      }
      if (!silencioso) {
        [dadoPateador, dadoArquero].forEach(function (dado) {
          dado.classList.remove("girando");
          void dado.offsetWidth;
          dado.classList.add("girando");
        });
      }
    }

    document.getElementById("tirar").onclick = function () { tirar(false); };
    document.getElementById("tirar-diez").onclick = function () {
      for (var i = 0; i < 10; i++) tirar(true);
    };

    pintarDado(dadoPateador, 1);
    pintarDado(dadoArquero, 6);
    elegir(elegida);
  }

  /* ── El partido grabado ─────────────────────────────────────────── */

  function reproductor() {
    var relato = document.getElementById("relato");
    if (!relato) return;

    var ESPERAS = [1500, 950, 600, 380, 190, 70];
    var marcador = document.getElementById("marcador");
    var minuto = document.getElementById("minuto");
    var velocidad = document.getElementById("velocidad");
    var detalles = document.getElementById("detalles");
    var partido = null, indice = 0, temporizador = null;

    function visibles() {
      if (!partido) return [];
      return partido.eventos.filter(function (ev) {
        if (/^Inicio reglamento=/.test(ev.texto || "")) return false;
        return detalles.checked ? ev.tier !== "noise" : ev.tier === "moment";
      });
    }

    /* El motor escribe el relato pensando en la terminal. Acá se lo deja
       más parecido a como lo contaría alguien mirando el partido. */
    var RETOQUES = [
      [/^T(\d+) \| (\S+) \| marcador .*/, "— Turno $1, la tiene $2"],
      [/^\*\* GOL de (\S+).*/, "¡GOL de $1!"],
      [/^>> Cambio de equipo.*/, "  Cambio de equipo: todos completan la mano"],
      [/^Empate (\d+)-(\d+): se define por penales.*/, "$1 a $2: se define por penales"],
      [/^Fin en penales: gana .*/, "Se define en los penales"],
      [/^Fin: gana .*/, "Termina el partido"],
      [/^Atajada o fuera$/, "  La ataja el arquero"],
    ];

    function comoTexto(ev) {
      var texto = (ev.texto || "").replace(/\s+$/, "");
      for (var i = 0; i < RETOQUES.length; i++) {
        if (RETOQUES[i][0].test(texto)) return texto.replace(RETOQUES[i][0], RETOQUES[i][1]);
      }
      return texto;
    }

    function paso() {
      var eventos = visibles();
      if (indice >= eventos.length) return false;
      var ev = eventos[indice];
      var anterior = relato.querySelector(".actual");
      if (anterior) anterior.classList.remove("actual");

      var linea = document.createElement("li");
      linea.className = ev.tier + " " + ev.tipo + " actual";
      linea.textContent = comoTexto(ev);
      relato.appendChild(linea);
      relato.scrollTop = relato.scrollHeight;

      var marca = (ev.texto || "").match(/marcador (\d+)-(\d+)/) ||
                  (ev.texto || "").match(/Marcador: .*? (\d+) - (\d+)/);
      if (marca) marcador.textContent = marca[1] + " – " + marca[2];
      if (ev.turno) minuto.textContent = "turno " + ev.turno + " de " + partido.turnos;

      indice++;
      return true;
    }

    function reproducir() {
      if (!paso()) { pausar(); return; }
      temporizador = setTimeout(reproducir, ESPERAS[parseInt(velocidad.value, 10) - 1]);
    }

    function pausar() { clearTimeout(temporizador); temporizador = null; }

    function reiniciar() {
      pausar();
      indice = 0;
      relato.innerHTML = "";
      marcador.textContent = "0 – 0";
      minuto.textContent = "turno 0 de " + (partido ? partido.turnos : 0);
    }

    document.getElementById("reproducir").onclick = function () { pausar(); reproducir(); };
    document.getElementById("pausar").onclick = pausar;
    document.getElementById("siguiente").onclick = function () { pausar(); paso(); };
    document.getElementById("reiniciar").onclick = reiniciar;
    detalles.onchange = reiniciar;

    fetch("replays/partido.json")
      .then(function (r) { if (!r.ok) throw new Error("no se pudo leer el partido"); return r.json(); })
      .then(function (datos) {
        partido = datos;
        document.getElementById("equipo-1").textContent = datos.equipos[0].join(", ");
        document.getElementById("equipo-2").textContent = datos.equipos[1].join(", ");
        reiniciar();
        arrancarCuandoSeVea();
      })
      .catch(function (error) {
        relato.innerHTML = "<li>" + error.message + "</li>";
      });

    /* Arranca solo cuando la sección entra en pantalla. */
    function arrancarCuandoSeVea() {
      if (!("IntersectionObserver" in window)) return;
      var seccion = document.getElementById("partido");
      var observador = new IntersectionObserver(function (entradas) {
        entradas.forEach(function (entrada) {
          if (entrada.isIntersecting && indice === 0) {
            reproducir();
            observador.disconnect();
          }
        });
      }, { threshold: 0.35 });
      observador.observe(seccion);
    }
  }

  /* ── Navegación ─────────────────────────────────────────────────── */

  function navegacion() {
    var pagina = location.pathname.split("/").pop() || "index.html";
    document.querySelectorAll(".barra nav a").forEach(function (enlace) {
      var destino = enlace.getAttribute("href");
      if (destino === pagina) enlace.classList.add("activa");
    });

    if (!location.hostname.endsWith(".github.io")) return;
    var usuario = location.hostname.replace(".github.io", "");
    var repo = location.pathname.split("/").filter(Boolean)[0];
    if (!repo) return;
    var base = "https://github.com/" + usuario + "/" + repo;
    var enlaceRepo = document.getElementById("enlace-repo");
    if (enlaceRepo) enlaceRepo.href = base;
    document.querySelectorAll('a[href$=".md"]').forEach(function (enlace) {
      enlace.href = base + "/blob/Fobal3/docs/" + enlace.getAttribute("href").replace(/^\.\//, "");
    });
  }

  navegacion();
  laboratorioDelDado();
  reproductor();
})();
