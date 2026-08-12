/* Fobal Facu — interfaz de simulaciones.
   El estado del juego vive en el servidor: acá se arman los equipos, se editan
   los reglamentos, se piden simulaciones y se dibujan los resultados. */

"use strict";

var COLORES_SERIE = ["--dato-1", "--dato-2", "--dato-3", "--dato-4", "--dato-5", "--dato-6"];
var ESPERAS = [1500, 950, 600, 380, 190, 70];

var NOMBRES_ACCION = {
  pase: "pasar la pelota",
  disparo: "patear al arco",
  reventar: "reventar la pelota (sin carta)",
  pasa_turno: "pasar de turno (sin carta)",
};

var app = {
  opciones: null,
  reglamentoActual: null,
  borrador: null,
  partido: null,
  reproduccion: { indice: 0, temporizador: null },
};

/* ── utilidades ────────────────────────────────────────────────────── */

function $(id) { return document.getElementById(id); }

function el(etiqueta, props, hijos) {
  var nodo = document.createElement(etiqueta);
  props = props || {};
  Object.keys(props).forEach(function (clave) {
    var valor = props[clave];
    if (clave === "clase") nodo.className = valor;
    else if (clave === "texto") nodo.textContent = valor;
    else if (clave === "html") nodo.innerHTML = valor;
    else if (clave.indexOf("on") === 0) nodo.addEventListener(clave.slice(2), valor);
    else if (valor !== null && valor !== undefined) nodo.setAttribute(clave, valor);
  });
  [].concat(hijos || []).forEach(function (hijo) { if (hijo) nodo.append(hijo); });
  return nodo;
}

function opcionesDe(select, valores, etiquetas) {
  select.innerHTML = "";
  valores.forEach(function (valor) {
    select.append(el("option", { value: valor, texto: (etiquetas || {})[valor] || valor }));
  });
}

function api(ruta, opciones) {
  return fetch(ruta, Object.assign({ headers: { "Content-Type": "application/json" } }, opciones || {}))
    .then(function (respuesta) {
      return respuesta.json().catch(function () { return {}; }).then(function (datos) {
        if (!respuesta.ok) throw new Error(datos.error || ("error " + respuesta.status));
        return datos;
      });
    });
}

var temporizadorAviso = null;
function avisar(mensaje, esError) {
  var aviso = $("aviso");
  aviso.textContent = mensaje;
  aviso.className = esError ? "aviso error" : "aviso";
  aviso.hidden = false;
  clearTimeout(temporizadorAviso);
  temporizadorAviso = setTimeout(function () { aviso.hidden = true; }, 3400);
}

function numero(valor, porDefecto) {
  var n = Number(valor);
  return isFinite(n) ? n : porDefecto;
}

function mostrarVista(nombre) {
  document.querySelectorAll(".vista").forEach(function (v) {
    v.classList.toggle("activa", v.id === "vista-" + nombre);
  });
  document.querySelectorAll("#pestanas button").forEach(function (b) {
    b.setAttribute("aria-selected", String(b.dataset.vista === nombre));
  });
  window.scrollTo({ top: 0, behavior: "smooth" });
}

/* ── arranque ──────────────────────────────────────────────────────── */

function iniciar() {
  api("/api/opciones").then(function (opciones) {
    app.opciones = opciones;
    dibujarEquipos(opciones.equipos);
    prepararEditor();
    prepararSimulacion();
    dibujarListaReglamentos();
    var primero = opciones.reglamentos.filter(function (r) { return r.activo; })[0] ||
                  opciones.reglamentos[0];
    if (primero) cargarReglamento(primero.id);
    document.querySelectorAll("#pestanas button").forEach(function (boton) {
      boton.onclick = function () { mostrarVista(boton.dataset.vista); };
    });
    $("ir-a-reglas").onclick = function () { mostrarVista("reglas"); };
  }).catch(function (error) {
    document.body.prepend(el("p", { clase: "problemas", texto: "No se pudo hablar con el simulador: " + error.message }));
  });
}

/* ── equipos ───────────────────────────────────────────────────────── */

function dibujarEquipos(equipos) {
  var caja = $("equipos");
  caja.innerHTML = "";
  ["equipo1", "equipo2"].forEach(function (clave) {
    var equipo = equipos[clave];
    var panel = el("div", { clase: "panel" });
    panel.dataset.equipo = clave;

    panel.append(el("label", { texto: "Nombre del equipo" },
      el("input", { clase: "nombre-equipo-input", value: equipo.nombre, maxlength: "30" })));

    var jugadores = el("div", { clase: "jugadores" });
    equipo.jugadores.forEach(function (nombre) { jugadores.append(filaJugador(nombre)); });
    panel.append(jugadores);

    panel.append(el("button", {
      type: "button", clase: "accion suave", texto: "+ Agregar jugador",
      onclick: function () {
        if (jugadores.children.length >= 8) return avisar("Máximo 8 jugadores por equipo", true);
        jugadores.append(filaJugador(""));
        renumerar(jugadores);
        jugadores.lastChild.querySelector("input").focus();
      },
    }));
    caja.append(panel);
    renumerar(jugadores);
  });
}

function filaJugador(nombre) {
  var fila = el("div", { clase: "jugador" }, [
    el("span", { clase: "dorsal" }),
    el("input", { value: nombre, placeholder: "nombre", maxlength: "20" }),
  ]);
  fila.append(el("button", {
    type: "button", clase: "quitar", texto: "×", title: "Sacar del equipo",
    onclick: function () {
      var lista = fila.parentNode;
      if (lista.children.length <= 2) return avisar("Hacen falta al menos 2 jugadores", true);
      fila.remove();
      renumerar(lista);
    },
  }));
  return fila;
}

function renumerar(lista) {
  Array.prototype.forEach.call(lista.children, function (fila, i) {
    fila.querySelector(".dorsal").textContent = String(i + 1);
  });
}

function leerEquipos() {
  var salida = {};
  document.querySelectorAll("#equipos .panel").forEach(function (panel) {
    salida[panel.dataset.equipo] = {
      nombre: panel.querySelector(".nombre-equipo-input").value.trim(),
      jugadores: Array.prototype.map.call(
        panel.querySelectorAll(".jugadores input"),
        function (i) { return i.value.trim(); }
      ).filter(Boolean),
    };
  });
  return salida;
}

/* ── editor de reglamentos ─────────────────────────────────────────── */

function dibujarListaReglamentos() {
  var lista = $("lista-reglamentos");
  lista.innerHTML = "";
  app.opciones.reglamentos.forEach(function (reg) {
    var boton = el("button", {
      type: "button",
      clase: reg.id === app.reglamentoActual ? "activa" : "",
      onclick: function () { cargarReglamento(reg.id); },
    }, [
      el("span", { clase: "id", texto: (reg.activo ? "● " : "○ ") + reg.id }),
      el("span", { clase: "detalle", texto: reg.nombre + " · " + reg.cartas + " cartas" }),
    ]);
    lista.append(el("li", {}, boton));
  });
}

function cargarReglamento(id) {
  api("/api/reglamentos/" + encodeURIComponent(id)).then(function (datos) {
    app.reglamentoActual = id;
    app.borrador = datos;
    poblarFormulario(datos);
    dibujarListaReglamentos();
    $("estado-reglas").textContent = "";
  }).catch(function (error) { avisar(error.message, true); });
}

function prepararEditor() {
  var o = app.opciones;

  var acciones = $("acciones");
  acciones.innerHTML = "";
  o.acciones.forEach(function (accion) {
    acciones.append(el("label", { clase: "casilla" }, [
      el("input", { type: "checkbox", value: accion, onchange: revisar }),
      document.createTextNode(NOMBRES_ACCION[accion] || accion),
    ]));
  });

  ["pase", "pasa_turno"].forEach(function (contexto) {
    var caja = $("reac-" + contexto);
    caja.innerHTML = "";
    o.cartas_defensivas.forEach(function (carta) {
      caja.append(el("label", { clase: "casilla" }, [
        el("input", {
          type: "checkbox", value: carta,
          onchange: function () { dibujarContras(); revisar(); },
        }),
        document.createTextNode(carta),
      ]));
    });
  });

  var tabla = $("tabla-disparo");
  tabla.innerHTML = "";
  o.tabla_disparo.forEach(function (franja) {
    tabla.append(el("tr", {}, [
      el("td", { texto: franja.pases === 4 ? "4 o más" : String(franja.pases) }),
      el("td", { texto: rango(franja.gol) }),
      el("td", { texto: rango(franja.ataja) }),
    ]));
  });

  var agregar = $("agregar-carta");
  agregar.onchange = function () {
    if (!agregar.value) return;
    var mazo = leerMazo();
    mazo[agregar.value] = 2;
    dibujarMazo(mazo);
    revisar();
  };

  $("formulario").addEventListener("input", revisar);
  $("btn-guardar").onclick = function () { guardarReglamento(); };
  $("btn-guardar-simular").onclick = function () {
    guardarReglamento().then(function (id) {
      if (!id) return;
      mostrarVista("simular");
      var primero = document.querySelector("#escenarios select");
      if (primero) primero.value = id;
      correrSimulacion();
    });
  };
  $("btn-descartar").onclick = function () {
    if (app.reglamentoActual) cargarReglamento(app.reglamentoActual);
  };
  $("btn-nuevo").onclick = function () {
    api("/api/reglamentos/_nuevo").then(function (datos) {
      app.reglamentoActual = null;
      app.borrador = datos;
      poblarFormulario(datos);
      dibujarListaReglamentos();
      $("r-id").focus();
      avisar("Reglamento nuevo: ponele un id y guardalo");
    });
  };
  $("btn-copiar").onclick = function () {
    var copia = leerFormulario();
    copia.id = copia.id + "-copia";
    copia.nombre = copia.nombre + " (copia)";
    copia.activo = false;
    app.reglamentoActual = null;
    app.borrador = copia;
    poblarFormulario(copia);
    avisar("Copia lista: cambiale el id y guardala");
  };
  $("btn-borrar").onclick = function () {
    var id = $("r-id").value.trim();
    if (!confirm("¿Borrar el reglamento " + id + "? Se elimina el archivo.")) return;
    api("/api/reglamentos/" + encodeURIComponent(id), { method: "DELETE" })
      .then(function () { return refrescarCatalogo(); })
      .then(function () {
        var primero = app.opciones.reglamentos[0];
        if (primero) cargarReglamento(primero.id);
        avisar("Borrado " + id);
      })
      .catch(function (error) { avisar(error.message, true); });
  };

  $("guardar-equipos").onclick = function () {
    api("/api/equipos", { method: "POST", body: JSON.stringify(leerEquipos()) })
      .then(function (equipos) {
        app.opciones.equipos = equipos;
        dibujarEquipos(equipos);
        $("estado-equipos").textContent = "guardado";
        avisar("Equipos guardados");
      })
      .catch(function (error) { avisar(error.message, true); });
  };
}

function rango(par) { return par[0] === par[1] ? String(par[0]) : par[0] + " a " + par[1]; }

function refrescarCatalogo() {
  return api("/api/opciones").then(function (opciones) {
    app.opciones = opciones;
    dibujarListaReglamentos();
    document.querySelectorAll("select.selector-reglamento").forEach(function (select) {
      var elegido = select.value;
      opcionesDe(select, opciones.reglamentos.map(function (r) { return r.id; }));
      select.value = elegido;
    });
  });
}

function poblarFormulario(reg) {
  $("r-id").value = reg.id || "";
  $("r-nombre").value = reg.nombre || "";
  $("r-version").value = reg.version || "";
  $("r-descripcion").value = reg.descripcion || "";
  $("r-documento").value = reg.documento || "";
  $("r-activo").checked = reg.activo !== false;

  dibujarMazo(reg.mazo);

  $("p-goles").value = reg.partido.goles_para_ganar;
  $("p-penales-0").value = reg.partido.penales_si_marcador[0];
  $("p-penales-1").value = reg.partido.penales_si_marcador[1];
  $("p-mano").value = reg.partido.mano_inicial;
  $("p-minimo").value = reg.partido.jugadores_minimo_por_equipo;
  $("p-reposicion").value = reg.reposicion;

  document.querySelectorAll("#acciones input").forEach(function (casilla) {
    casilla.checked = reg.acciones_ofensivas.indexOf(casilla.value) !== -1;
  });
  ["pase", "pasa_turno"].forEach(function (contexto) {
    var cartas = (reg.reacciones[contexto] || {}).cartas || [];
    document.querySelectorAll("#reac-" + contexto + " input").forEach(function (casilla) {
      casilla.checked = cartas.indexOf(casilla.value) !== -1;
    });
  });
  dibujarContras();
  ["pase", "pasa_turno"].forEach(function (contexto) {
    var contra = (reg.reacciones[contexto] || {}).contra || {};
    document.querySelectorAll("#contra-" + contexto + " select").forEach(function (select) {
      if (contra[select.dataset.carta]) select.value = contra[select.dataset.carta];
    });
  });

  $("r-falta").value = Math.round((reg.reglas.prob_falta_por_turno || 0) * 100);
  $("r-sin-respuesta").value = reg.reglas.pasa_turno_sin_respuesta;
  $("r-rebote").checked = !!reg.disparo.rebote_palo;
  $("r-reventar").checked = !!reg.reglas.reventar_habilitado;
  $("r-encadenables").checked = !!reg.reglas.reacciones_encadenables;
  $("r-una-reaccion").checked = !!reg.reglas.una_reaccion_defensiva_por_accion;
  $("r-trampa-solo").checked = !!reg.reglas.trampa_marca_solo_en_pasa_turno;
  $("r-motor").value = reg.motor_perfil || "v1";
  revisar();
}

function dibujarMazo(mazo) {
  var caja = $("mazo");
  caja.innerHTML = "";
  var roles = {};
  app.opciones.cartas.forEach(function (c) { roles[c.nombre] = c.rol; });

  Object.keys(mazo).forEach(function (carta) {
    var entrada = el("input", {
      type: "number", min: "0", max: "200", value: mazo[carta],
      oninput: function () { actualizarTotal(); },
    });
    var barra = el("span", {});
    var fila = el("div", { clase: "carta-fila" }, [
      el("span", { clase: "nombre-carta" }, [
        el("span", { clase: "marca-rol", style: "background:" + colorRol(roles[carta]) }),
        document.createTextNode(carta),
      ]),
      el("span", { clase: "paso-cantidad" }, [
        el("button", { type: "button", texto: "−", title: "Una menos",
          onclick: function () { entrada.value = Math.max(0, numero(entrada.value, 0) - 1); actualizarTotal(); revisar(); } }),
        entrada,
        el("button", { type: "button", texto: "+", title: "Una más",
          onclick: function () { entrada.value = numero(entrada.value, 0) + 1; actualizarTotal(); revisar(); } }),
      ]),
      el("span", { clase: "pista-carta" }, barra),
    ]);
    fila.append(el("button", {
      type: "button", clase: "quitar", texto: "×", title: "Sacar del mazo",
      onclick: function () { fila.remove(); actualizarTotal(); dibujarMazo(leerMazo()); revisar(); },
    }));
    fila.dataset.carta = carta;
    caja.append(fila);
  });
  actualizarTotal();

  var usadas = Object.keys(mazo);
  var libres = app.opciones.cartas
    .map(function (c) { return c.nombre; })
    .filter(function (n) { return usadas.indexOf(n) === -1; });
  opcionesDe($("agregar-carta"), [""].concat(libres), { "": "elegir…" });
}

function colorRol(rol) {
  if (rol === "ofensiva") return "var(--cesped)";
  if (rol === "defensiva") return "var(--robo)";
  return "var(--tinta-3)";
}

function leerMazo() {
  var mazo = {};
  Array.prototype.forEach.call($("mazo").children, function (fila) {
    mazo[fila.dataset.carta] = numero(fila.querySelector("input").value, 0);
  });
  return mazo;
}

function actualizarTotal() {
  var mazo = leerMazo();
  var total = Object.keys(mazo).reduce(function (a, k) { return a + mazo[k]; }, 0);
  $("total-mazo").textContent = total;
  Array.prototype.forEach.call($("mazo").children, function (fila) {
    var porcentaje = total ? (100 * mazo[fila.dataset.carta]) / total : 0;
    fila.querySelector(".pista-carta > span").style.width = porcentaje + "%";
    fila.querySelector(".pista-carta").title = porcentaje.toFixed(1) + "% del mazo";
  });
}

function seleccionadas(idCaja) {
  return Array.prototype.map.call(
    $(idCaja).querySelectorAll("input:checked"), function (i) { return i.value; }
  );
}

function dibujarContras() {
  var previas = leerContras();
  ["pase", "pasa_turno"].forEach(function (contexto) {
    var caja = $("contra-" + contexto);
    caja.innerHTML = "";
    var elegidas = seleccionadas("reac-" + contexto);
    if (!elegidas.length) return;
    caja.append(el("h3", { texto: "El ataque la puede anular con:" }));
    elegidas.forEach(function (carta) {
      var select = el("select", { onchange: revisar });
      opcionesDe(select, [""].concat(app.opciones.cartas_contra), { "": "no se anula" });
      select.dataset.carta = carta;
      select.value = (previas[contexto] || {})[carta] || "";
      caja.append(el("label", {}, [document.createTextNode(carta), select]));
    });
  });
}

function leerContras() {
  var salida = {};
  ["pase", "pasa_turno"].forEach(function (contexto) {
    salida[contexto] = {};
    $("contra-" + contexto).querySelectorAll("select").forEach(function (select) {
      if (select.value) salida[contexto][select.dataset.carta] = select.value;
    });
  });
  return salida;
}

function leerFormulario() {
  var contras = leerContras();
  var base = app.borrador || {};
  return {
    id: $("r-id").value.trim(),
    nombre: $("r-nombre").value.trim(),
    version: $("r-version").value.trim() || "1.0",
    descripcion: $("r-descripcion").value.trim(),
    documento: $("r-documento").value.trim() || null,
    activo: $("r-activo").checked,
    mazo: leerMazo(),
    partido: {
      jugadores_minimo_por_equipo: numero($("p-minimo").value, 2),
      mano_inicial: numero($("p-mano").value, 6),
      goles_para_ganar: numero($("p-goles").value, 3),
      penales_si_marcador: [numero($("p-penales-0").value, 2), numero($("p-penales-1").value, 2)],
    },
    reposicion: $("p-reposicion").value,
    disparo: { rebote_palo: $("r-rebote").checked },
    acciones_ofensivas: seleccionadas("acciones"),
    reacciones: {
      pase: {
        cartas: seleccionadas("reac-pase"),
        contra: contras.pase,
        permitir_tackle: ((base.reacciones || {}).pase || {}).permitir_tackle || false,
      },
      pasa_turno: {
        cartas: seleccionadas("reac-pasa_turno"),
        contra: contras.pasa_turno,
        permitir_tackle: seleccionadas("reac-pasa_turno").indexOf("Tackle") !== -1,
      },
    },
    reglas: {
      trampa_marca_solo_en_pasa_turno: $("r-trampa-solo").checked,
      una_reaccion_defensiva_por_accion: $("r-una-reaccion").checked,
      pasa_turno_sin_respuesta: $("r-sin-respuesta").value,
      prob_falta_por_turno: numero($("r-falta").value, 8) / 100,
      reventar_habilitado: $("r-reventar").checked,
      reacciones_encadenables: $("r-encadenables").checked,
    },
    motor_perfil: $("r-motor").value,
  };
}

var temporizadorRevision = null;
function revisar() {
  $("r-falta-valor").textContent = $("r-falta").value + "%";
  clearTimeout(temporizadorRevision);
  temporizadorRevision = setTimeout(function () {
    api("/api/revisar", { method: "POST", body: JSON.stringify(leerFormulario()) })
      .then(function (respuesta) { mostrarProblemas(respuesta.problemas || []); })
      .catch(function (error) { mostrarProblemas([error.message]); });
  }, 250);
}

function mostrarProblemas(problemas) {
  var caja = $("problemas");
  caja.hidden = problemas.length === 0;
  caja.innerHTML = "";
  if (!problemas.length) return;
  caja.append(el("strong", { texto: "Para poder guardar hay que arreglar esto:" }));
  caja.append(el("ul", {}, problemas.map(function (p) { return el("li", { texto: p }); })));
}

function guardarReglamento() {
  var datos = leerFormulario();
  return api("/api/reglamentos", { method: "POST", body: JSON.stringify(datos) })
    .then(function (respuesta) {
      return refrescarCatalogo().then(function () {
        app.reglamentoActual = respuesta.guardado;
        cargarReglamento(respuesta.guardado);
        $("estado-reglas").textContent = "guardado";
        avisar("Guardado " + respuesta.guardado);
        return respuesta.guardado;
      });
    })
    .catch(function (error) {
      avisar(error.message, true);
      return null;
    });
}

/* ── simulación ────────────────────────────────────────────────────── */

function prepararSimulacion() {
  agregarEscenario(0);
  agregarEscenario(1);
  $("btn-escenario").onclick = function () { agregarEscenario($("escenarios").children.length); };
  $("btn-correr").onclick = correrSimulacion;

  var reglamentos = app.opciones.reglamentos.map(function (r) { return r.id; });
  opcionesDe($("v-reglamento"), reglamentos);
  $("v-reglamento").classList.add("selector-reglamento");
  var activo = app.opciones.reglamentos.filter(function (r) { return r.activo; })[0];
  if (activo) $("v-reglamento").value = activo.id;
  perfilesEn($("v-perfil"));

  $("btn-jugar").onclick = jugarPartido;
  $("btn-reproducir").onclick = function () { pausar(); reproducir(); };
  $("btn-pausar").onclick = pausar;
  $("btn-siguiente").onclick = function () { pausar(); pasoRelato(); };
  $("btn-reiniciar").onclick = reiniciarRelato;
  $("v-detalles").onchange = reiniciarRelato;
}

function perfilesEn(select) {
  var etiquetas = {};
  app.opciones.perfiles.forEach(function (p) { etiquetas[p.id] = p.nombre; });
  opcionesDe(select, app.opciones.perfiles.map(function (p) { return p.id; }), etiquetas);
  select.value = "estrategica";
}

function agregarEscenario(indice) {
  var activos = app.opciones.reglamentos.filter(function (r) { return r.activo; });
  var elegido = activos[indice] || app.opciones.reglamentos[indice] || app.opciones.reglamentos[0];

  var selectReglamento = el("select", { clase: "selector-reglamento" });
  opcionesDe(selectReglamento, app.opciones.reglamentos.map(function (r) { return r.id; }));
  if (elegido) selectReglamento.value = elegido.id;

  var selectPerfil = el("select", {});
  perfilesEn(selectPerfil);

  var fila = el("div", { clase: "escenario" }, [
    el("label", { texto: "Reglamento" }, selectReglamento),
    el("label", { texto: "Jugadores por equipo" }, el("input", { type: "number", min: "2", max: "8", value: "3" })),
    el("label", { texto: "Estilo de juego" }, selectPerfil),
  ]);
  fila.append(el("button", {
    type: "button", clase: "quitar", texto: "×", title: "Sacar esta comparación",
    onclick: function () { fila.remove(); },
  }));
  $("escenarios").append(fila);
}

function leerEscenarios() {
  return Array.prototype.map.call($("escenarios").children, function (fila) {
    var campos = fila.querySelectorAll("select, input");
    return {
      reglamento: campos[0].value,
      jugadores_por_equipo: numero(campos[1].value, 3),
      ia: campos[2].value,
    };
  });
}

function correrSimulacion() {
  var escenarios = leerEscenarios();
  if (!escenarios.length) return avisar("Agregá al menos un reglamento", true);
  var partidos = numero($("partidos").value, 200);
  $("estado-simulacion").textContent = "simulando " + (escenarios.length * partidos) + " partidos…";
  $("btn-correr").disabled = true;

  api("/api/simular", { method: "POST", body: JSON.stringify({ escenarios: escenarios, partidos: partidos }) })
    .then(function (datos) {
      dibujarResultados(datos.resultados, datos.partidos);
      $("estado-simulacion").textContent = "listo";
    })
    .catch(function (error) {
      $("estado-simulacion").textContent = "";
      avisar(error.message, true);
    })
    .then(function () { $("btn-correr").disabled = false; });
}

function dibujarResultados(resultados, partidos) {
  var caja = $("resultados");
  caja.innerHTML = "";
  if (!resultados.length) return;

  resultados.forEach(function (r) {
    var panel = el("div", { clase: "panel" });
    panel.append(el("h3", { texto: r.etiqueta }));
    panel.append(el("p", { clase: "ayuda", texto: partidos + " partidos simulados" }));
    panel.append(el("div", { clase: "tarjetas" }, [
      tarjeta(r.pct_completados + " %", "de los partidos se definen", "el resto se traba"),
      tarjeta(r.goles_promedio, "goles por partido", "los dos equipos juntos"),
      tarjeta(r.turnos_promedio, "turnos por partido", "cuánto dura"),
      tarjeta(r.pct_penales + " %", "se define por penales", "llegaron al 2-2"),
    ]));

    var reparto = el("div", { clase: "grafico" });
    reparto.append(el("h4", { texto: "En qué se va el juego" }));
    reparto.append(barraApilada(r));
    reparto.append(leyendaAcciones(r));
    panel.append(reparto);
    caja.append(panel);
  });

  if (resultados.length > 1) {
    var comparacion = el("div", { clase: "panel" });
    comparacion.append(el("h3", { texto: "Comparación" }));
    comparacion.append(grafico("Partidos que se definen", "más es mejor: menos partidos trabados",
      resultados, function (r) { return r.pct_completados; }, function (v) { return v.toFixed(1) + " %"; }, 100));
    comparacion.append(grafico("Turnos por partido", "cuánto dura cada uno",
      resultados, function (r) { return r.turnos_promedio; }, function (v) { return v.toFixed(0); }));
    comparacion.append(grafico("Goles por partido", "",
      resultados, function (r) { return r.goles_promedio; }, function (v) { return v.toFixed(2); }));
    comparacion.append(grafico("Se definen por penales", "",
      resultados, function (r) { return r.pct_penales; }, function (v) { return v.toFixed(1) + " %"; }, 100));
    caja.append(comparacion);
  }

  caja.append(tablaDetalle(resultados));
}

function tarjeta(valor, rotulo, pie) {
  return el("div", { clase: "tarjeta" }, [
    el("div", { clase: "valor", texto: String(valor) }),
    el("div", { clase: "rotulo", texto: rotulo }),
    el("div", { clase: "pie", texto: pie || "" }),
  ]);
}

function grafico(titulo, aclaracion, resultados, valorDe, formato, maximoFijo) {
  var valores = resultados.map(valorDe);
  var maximo = maximoFijo || Math.max.apply(null, valores.concat([0.001]));
  var filas = resultados.map(function (r, i) {
    var ancho = Math.max(1, (100 * valores[i]) / maximo);
    return el("div", { clase: "fila-barra" }, [
      el("span", { texto: r.etiqueta }),
      el("div", { clase: "pista", title: r.etiqueta + ": " + formato(valores[i]) },
        el("div", { clase: "relleno", style: "width:" + ancho + "%;background:var(" + COLORES_SERIE[i % 6] + ")" })),
      el("span", { clase: "cifra", texto: formato(valores[i]) }),
    ]);
  });
  return el("div", { clase: "grafico" }, [
    el("h4", { texto: titulo }),
    aclaracion ? el("p", { clase: "aclaracion", texto: aclaracion }) : null,
  ].concat(filas));
}

function barraApilada(resultado) {
  var acciones = app.opciones.acciones_reporte;
  var segmentos = acciones.map(function (accion, i) {
    var valor = resultado.reparto_acciones[accion] || 0;
    if (!valor) return null;
    return el("span", {
      style: "width:" + valor + "%;background:var(" + COLORES_SERIE[i % 6] + ")",
      title: etiquetaAccion(accion) + ": " + valor + "%",
    });
  }).filter(Boolean);
  return el("div", { clase: "apilada" }, segmentos);
}

function leyendaAcciones(resultado) {
  var acciones = app.opciones.acciones_reporte;
  return el("div", { clase: "leyenda" }, acciones.map(function (accion, i) {
    var valor = resultado.reparto_acciones[accion] || 0;
    if (!valor) return null;
    return el("span", {}, [
      el("i", { style: "background:var(" + COLORES_SERIE[i % 6] + ")" }),
      document.createTextNode(etiquetaAccion(accion) + " " + valor + "%"),
    ]);
  }).filter(Boolean));
}

function etiquetaAccion(accion) {
  return (app.opciones.etiquetas_accion || {})[accion] || accion;
}

function tablaDetalle(resultados) {
  var columnas = [
    ["Escenario", function (r) { return r.etiqueta; }],
    ["Se definen", function (r) { return r.pct_completados + " %"; }],
    ["Goles", function (r) { return r.goles_promedio; }],
    ["Turnos", function (r) { return r.turnos_promedio; }],
    ["Penales", function (r) { return r.pct_penales + " %"; }],
    ["Trampas puestas", function (r) { return r.por_partido.trampa_colocada; }],
    ["Marcas puestas", function (r) { return r.por_partido.marca_colocada; }],
    ["Offsides cobrados", function (r) { return r.por_partido.offside_efectivo; }],
    ["Victorias 1 / 2", function (r) { return r.victorias[0] + " / " + r.victorias[1]; }],
  ];
  var tabla = el("table", { clase: "datos" });
  tabla.append(el("thead", {}, el("tr", {}, columnas.map(function (c) { return el("th", { texto: c[0] }); }))));
  tabla.append(el("tbody", {}, resultados.map(function (r) {
    return el("tr", {}, columnas.map(function (c, i) {
      return el(i === 0 ? "th" : "td", { texto: String(c[1](r)) });
    }));
  })));
  return el("div", { clase: "panel" }, [
    el("h3", { texto: "Todos los números" }),
    el("p", { clase: "ayuda", texto: "Las trampas y marcas se cuentan por partido." }),
    el("div", { clase: "desplaza" }, tabla),
  ]);
}

/* ── ver un partido ────────────────────────────────────────────────── */

function jugarPartido() {
  var cuerpo = {
    escenario: {
      reglamento: $("v-reglamento").value,
      jugadores_por_equipo: numero($("v-jugadores").value, 3),
      ia: $("v-perfil").value,
    },
    semilla: $("v-semilla").value.trim(),
    equipos: leerEquipos(),
  };
  $("estado-partido").textContent = "jugando…";
  api("/api/partido", { method: "POST", body: JSON.stringify(cuerpo) })
    .then(function (partido) {
      app.partido = partido;
      $("estado-partido").textContent = "";
      $("panel-partido").hidden = false;
      $("v-semilla").value = partido.semilla;
      $("nombre-equipo-1").textContent = partido.nombres_equipos[0];
      $("nombre-equipo-2").textContent = partido.nombres_equipos[1];
      reiniciarRelato();
      reproducir();
    })
    .catch(function (error) {
      $("estado-partido").textContent = "";
      avisar(error.message, true);
    });
}

function eventosVisibles() {
  if (!app.partido) return [];
  return app.partido.eventos.filter(function (ev) {
    if (/^Inicio reglamento=/.test(ev.texto || "")) return false;
    return $("v-detalles").checked ? ev.tier !== "noise" : ev.tier === "moment";
  });
}

var RETOQUES = [
  [/^T(\d+) \| (\S+) \| marcador .*/, "— Turno $1, la tiene $2"],
  [/^\*\* GOL de (\S+).*/, "¡GOL de $1!"],
  [/^>> Cambio de equipo.*/, "  Cambio de equipo: todos completan la mano"],
  [/^Empate (\d+)-(\d+): se define por penales.*/, "$1 a $2: se define por penales"],
  [/^Fin en penales: gana .*/, "Se define en los penales"],
  [/^Fin: gana .*/, "Termina el partido"],
];

function comoTexto(ev) {
  var texto = (ev.texto || "").replace(/\s+$/, "");
  for (var i = 0; i < RETOQUES.length; i++) {
    if (RETOQUES[i][0].test(texto)) return texto.replace(RETOQUES[i][0], RETOQUES[i][1]);
  }
  return texto;
}

function pasoRelato() {
  var eventos = eventosVisibles();
  var indice = app.reproduccion.indice;
  if (indice >= eventos.length) return false;
  var ev = eventos[indice];

  var relato = $("relato");
  var anterior = relato.querySelector(".actual");
  if (anterior) anterior.classList.remove("actual");
  relato.append(el("li", { clase: ev.tier + " " + ev.tipo + " actual", texto: comoTexto(ev) }));
  relato.scrollTop = relato.scrollHeight;

  var marca = (ev.texto || "").match(/marcador (\d+)-(\d+)/);
  if (marca) $("tanteador").textContent = marca[1] + " – " + marca[2];
  if (ev.turno) $("minuto").textContent = "turno " + ev.turno + " de " + app.partido.turnos;
  dibujarMesa(ev);

  app.reproduccion.indice = indice + 1;
  return true;
}

function dibujarMesa(ev) {
  var mesa = $("mesa");
  mesa.innerHTML = "";
  var cuentas = ev.cartas_por_jugador || {};
  var equipos = app.partido.equipos;

  equipos.forEach(function (jugadores, numeroEquipo) {
    jugadores.forEach(function (nombre) {
      var tienePelota = nombre === ev.portador;
      mesa.append(el("div", { clase: "jugador-mesa" + (tienePelota ? " tiene-pelota" : "") }, [
        el("span", { clase: "pelotita", texto: tienePelota ? "⚽" : "" }),
        el("span", { texto: nombre + (numeroEquipo === 0 ? "" : " ") }),
        el("span", { clase: "cuenta", texto: (cuentas[nombre] || 0) + " cartas" }),
      ]));
    });
  });

  $("titulo-mano").textContent = "La mano de " + (ev.portador || "—");
  var mano = $("mano");
  mano.innerHTML = "";
  var cartas = ev.mano || [];
  if (!cartas.length) {
    mano.append(el("p", { clase: "mano-vacia", texto: "Sin cartas en la mano." }));
    return;
  }
  var roles = {};
  app.opciones.cartas.forEach(function (c) { roles[c.nombre] = c.rol; });
  cartas.slice().sort().forEach(function (carta) {
    mano.append(el("div", { clase: "mini-carta " + (roles[carta] || "neutral"), texto: carta }));
  });
}

function reproducir() {
  if (!pasoRelato()) { pausar(); return; }
  app.reproduccion.temporizador = setTimeout(reproducir, ESPERAS[numero($("v-velocidad").value, 4) - 1]);
}

function pausar() {
  clearTimeout(app.reproduccion.temporizador);
  app.reproduccion.temporizador = null;
}

function reiniciarRelato() {
  pausar();
  app.reproduccion.indice = 0;
  $("relato").innerHTML = "";
  $("mesa").innerHTML = "";
  $("mano").innerHTML = "";
  $("tanteador").textContent = "0 – 0";
  if (app.partido) $("minuto").textContent = "turno 0 de " + app.partido.turnos;
}

iniciar();
