/* Fobal Facu — banco de pruebas.
   Todo el estado del juego vive en el servidor: esta página solo edita
   reglamentos, pide simulaciones y dibuja los resultados. */

"use strict";

const ACCIONES_REPARTO = ["pase", "robo", "reventar", "disparo", "falta", "pasa_turno"];
const SERIES = ["--serie-1", "--serie-2", "--serie-3", "--serie-4", "--serie-5", "--serie-6"];
const ESPERAS = [1600, 1000, 650, 400, 200, 70];

const TEXTOS_MOMENTO = {
  cambio_equipo: "Cuando la pelota pasa de un equipo al otro.",
  mano_vacia: "Cuando un jugador se queda sin cartas.",
  fin_de_turno: "Al terminar cada turno.",
  al_jugar_carta: "Apenas alguien juega una carta, la repone.",
  nunca: "Nunca: se juega con lo repartido hasta que se acaba.",
};
const TEXTOS_QUIEN = {
  todos: "todos los jugadores",
  equipo_con_pelota: "solo el equipo que tiene la pelota",
  equipo_sin_pelota: "solo el equipo que no la tiene",
  el_jugador: "solo el jugador involucrado",
};
const NOMBRES_ACCION = {
  pase: "pasar la pelota",
  disparo: "patear al arco",
  reventar: "reventar la pelota (sin carta)",
  pasa_turno: "pasar de turno (sin carta)",
};
const NOMBRES_SIN_RESPUESTA = {
  nada: "no pasa nada: la pelota se queda donde está",
  pasa_companero: "la pelota pasa a un compañero",
};

const app = {
  opciones: null,
  reglamentoActual: null,
  borrador: null,
  partido: null,
  reproduccion: { indice: 0, temporizador: null },
};

// ── utilidades ──────────────────────────────────────────────────────────

const $ = (id) => document.getElementById(id);

function el(etiqueta, props = {}, hijos = []) {
  const nodo = document.createElement(etiqueta);
  for (const [clave, valor] of Object.entries(props)) {
    if (clave === "clase") nodo.className = valor;
    else if (clave === "texto") nodo.textContent = valor;
    else if (clave === "html") nodo.innerHTML = valor;
    else if (clave.startsWith("on")) nodo.addEventListener(clave.slice(2), valor);
    else if (valor !== null && valor !== undefined) nodo.setAttribute(clave, valor);
  }
  for (const hijo of [].concat(hijos)) if (hijo) nodo.append(hijo);
  return nodo;
}

function opcionesSelect(select, valores, etiquetas = {}) {
  select.innerHTML = "";
  for (const valor of valores) {
    select.append(el("option", { value: valor, texto: etiquetas[valor] || valor }));
  }
}

async function api(ruta, opciones = {}) {
  const respuesta = await fetch(ruta, {
    headers: { "Content-Type": "application/json" },
    ...opciones,
  });
  const datos = await respuesta.json().catch(() => ({}));
  if (!respuesta.ok) throw new Error(datos.error || `error ${respuesta.status}`);
  return datos;
}

let temporizadorAviso = null;
function avisar(mensaje, esError = false) {
  const aviso = $("aviso");
  aviso.textContent = mensaje;
  aviso.className = esError ? "aviso error" : "aviso";
  aviso.hidden = false;
  clearTimeout(temporizadorAviso);
  temporizadorAviso = setTimeout(() => { aviso.hidden = true; }, 3200);
}

function numero(valor, porDefecto = 0) {
  const n = Number(valor);
  return Number.isFinite(n) ? n : porDefecto;
}

// ── arranque ────────────────────────────────────────────────────────────

async function iniciar() {
  try {
    app.opciones = await api("/api/opciones");
  } catch (error) {
    document.body.prepend(el("p", { clase: "errores", texto: `No se pudo hablar con el simulador: ${error.message}` }));
    return;
  }
  $("version").textContent = `versión ${app.opciones.version}`;

  opcionesSelect($("rep-momento"), app.opciones.momentos_reposicion, TEXTOS_MOMENTO);
  opcionesSelect($("rep-quien"), app.opciones.alcances_reposicion, TEXTOS_QUIEN);
  opcionesSelect($("regla-sin-respuesta"), app.opciones.pasa_turno_sin_respuesta, NOMBRES_SIN_RESPUESTA);
  dibujarAcciones();
  dibujarReacciones();
  conectarEditor();
  conectarSimulacion();
  conectarPartido();

  document.querySelectorAll("#pestanas button").forEach((boton) => {
    boton.onclick = () => mostrarVista(boton.dataset.vista);
  });

  dibujarListaReglamentos();
  const primero = app.opciones.reglamentos.find((r) => r.activo) || app.opciones.reglamentos[0];
  if (primero) await cargarReglamento(primero.id);
  agregarEscenario();
  agregarEscenario(1);
}

function mostrarVista(nombre) {
  document.querySelectorAll(".vista").forEach((v) => v.classList.toggle("activa", v.id === `vista-${nombre}`));
  document.querySelectorAll("#pestanas button").forEach((b) => b.classList.toggle("activa", b.dataset.vista === nombre));
}

async function refrescarCatalogo() {
  app.opciones = await api("/api/opciones");
  dibujarListaReglamentos();
  document.querySelectorAll("select.selector-reglamento").forEach((select) => {
    const elegido = select.value;
    opcionesSelect(select, app.opciones.reglamentos.map((r) => r.id));
    select.value = app.opciones.reglamentos.some((r) => r.id === elegido)
      ? elegido : (app.opciones.reglamentos[0]?.id ?? "");
  });
}

// ── lista de reglamentos ────────────────────────────────────────────────

function dibujarListaReglamentos() {
  const lista = $("lista-reglamentos");
  lista.innerHTML = "";
  for (const reg of app.opciones.reglamentos) {
    const boton = el("button", {
      type: "button",
      clase: reg.id === app.reglamentoActual ? "activa" : "",
      onclick: () => cargarReglamento(reg.id),
    });
    boton.append(el("span", { clase: "id", texto: `${reg.activo ? "● " : "○ "}${reg.id}` }));
    boton.append(el("span", { clase: "detalle", texto: `${reg.nombre} · ${reg.cartas} cartas` }));
    lista.append(el("li", {}, boton));
  }
}

async function cargarReglamento(id) {
  try {
    const datos = await api(`/api/reglamentos/${encodeURIComponent(id)}`);
    app.reglamentoActual = id;
    app.borrador = datos;
    poblarEditor(datos);
    dibujarListaReglamentos();
  } catch (error) {
    avisar(error.message, true);
  }
}

// ── editor ──────────────────────────────────────────────────────────────

function dibujarAcciones() {
  const caja = $("acciones");
  caja.innerHTML = "";
  for (const accion of app.opciones.acciones) {
    caja.append(el("label", { clase: "casilla" }, [
      el("input", { type: "checkbox", value: accion, onchange: validarEnVivo }),
      document.createTextNode(NOMBRES_ACCION[accion] || accion),
    ]));
  }
}

function cartasDefensivas() {
  return app.opciones.cartas.filter((c) => c.rol === "defensiva").map((c) => c.nombre);
}

function cartasOfensivas() {
  return app.opciones.cartas.filter((c) => c.rol === "ofensiva").map((c) => c.nombre);
}

function dibujarReacciones() {
  for (const contexto of ["pase", "pasa-turno"]) {
    const caja = $(`reac-${contexto}`);
    caja.innerHTML = "";
    for (const carta of cartasDefensivas()) {
      caja.append(el("label", { clase: "casilla" }, [
        el("input", {
          type: "checkbox", value: carta,
          onchange: () => { dibujarContras(); validarEnVivo(); },
        }),
        document.createTextNode(carta),
      ]));
    }
  }
}

/* Para cada carta defensiva elegida, con qué carta la puede anular el ataque. */
function dibujarContras() {
  const previas = leerContras();
  for (const contexto of ["pase", "pasa-turno"]) {
    const caja = $(`contra-${contexto}`);
    caja.innerHTML = "";
    const elegidas = seleccionadas(`reac-${contexto}`);
    // La marca se coloca en un contexto y se cobra en el pase: su contra se
    // configura siempre junto al pase.
    if (contexto === "pase" && !elegidas.includes("Marca personal")
        && seleccionadas("reac-pasa-turno").includes("Marca personal")) {
      elegidas.push("Marca personal");
    }
    if (!elegidas.length) continue;
    caja.append(el("h4", { texto: "El ataque la puede anular con:" }));
    for (const carta of elegidas) {
      const select = el("select", { onchange: validarEnVivo });
      opcionesSelect(select, ["", ...cartasOfensivas()], { "": "no se anula" });
      select.value = previas[contexto]?.[carta] || "";
      select.dataset.carta = carta;
      caja.append(el("label", {}, [document.createTextNode(carta), select]));
    }
  }
}

function seleccionadas(idCaja) {
  return [...$(idCaja).querySelectorAll("input:checked")].map((i) => i.value);
}

function leerContras() {
  const salida = {};
  for (const contexto of ["pase", "pasa-turno"]) {
    salida[contexto] = {};
    for (const select of $(`contra-${contexto}`).querySelectorAll("select")) {
      if (select.value) salida[contexto][select.dataset.carta] = select.value;
    }
  }
  return salida;
}

function poblarEditor(reg) {
  $("r-id").value = reg.id;
  $("r-nombre").value = reg.nombre || "";
  $("r-version").value = reg.version || "";
  $("r-descripcion").value = reg.descripcion || "";
  $("r-activo").checked = !!reg.activo;
  $("r-extends").textContent = reg.extends
    ? `Hereda de ${reg.extends}: al guardar se escriben solo las diferencias.`
    : "";

  dibujarMazo(reg.mazo);
  $("mano-inicial").value = reg.mano.inicial;
  $("mano-maxima").value = reg.mano.maxima;
  $("rep-momento").value = reg.reposicion.momento;
  $("rep-quien").value = reg.reposicion.quien;
  $("goles-ganar").value = reg.partido.goles_para_ganar;
  $("penales-0").value = reg.partido.penales_si_marcador[0];
  $("penales-1").value = reg.partido.penales_si_marcador[1];
  $("min-jugadores").value = reg.partido.jugadores_minimo_por_equipo;
  $("limite-turnos").value = reg.partido.limite_turnos;
  $("disparo-rebote").checked = !!reg.disparo.rebote;
  $("disparo-palo").checked = !!reg.disparo.palo;
  dibujarTablaDisparo(reg.disparo.tabla);

  for (const casilla of $("acciones").querySelectorAll("input")) {
    casilla.checked = reg.acciones_ofensivas.includes(casilla.value);
  }
  for (const [contexto, clave] of [["pase", "pase"], ["pasa-turno", "pasa_turno"]]) {
    const cartas = reg.reacciones?.[clave]?.cartas || [];
    for (const casilla of $(`reac-${contexto}`).querySelectorAll("input")) {
      casilla.checked = cartas.includes(casilla.value);
    }
  }
  dibujarContras();
  for (const [contexto, clave] of [["pase", "pase"], ["pasa-turno", "pasa_turno"]]) {
    const contras = reg.reacciones?.[clave]?.contra || {};
    for (const select of $(`contra-${contexto}`).querySelectorAll("select")) {
      if (contras[select.dataset.carta]) select.value = contras[select.dataset.carta];
    }
  }

  $("regla-sin-respuesta").value = reg.reglas.pasa_turno_sin_respuesta;
  $("regla-falta").value = Math.round(reg.reglas.prob_falta_por_jugador * 100);
  $("regla-encadenables").checked = !!reg.reglas.reacciones_encadenables;
  actualizarAyudas();
  validarEnVivo();
}

function dibujarMazo(mazo) {
  const caja = $("mazo-filas");
  caja.innerHTML = "";
  for (const [carta, cantidad] of Object.entries(mazo)) filaDeMazo(caja, carta, cantidad);
  actualizarTotalMazo();

  const usadas = new Set(Object.keys(mazo));
  const agregar = $("mazo-agregar");
  opcionesSelect(agregar, ["", ...app.opciones.cartas.map((c) => c.nombre).filter((c) => !usadas.has(c))],
    { "": "elegir carta…" });
}

function filaDeMazo(caja, carta, cantidad) {
  const entrada = el("input", {
    type: "number", min: "0", max: "200", value: cantidad,
    oninput: () => { actualizarTotalMazo(); validarEnVivo(); },
  });
  const barra = el("span", {});
  const fila = el("div", { clase: "carta-fila" }, [
    el("span", { clase: "nombre", texto: carta }),
    entrada,
    el("div", { clase: "barra-mazo" }, barra),
    el("button", {
      type: "button", clase: "quitar", title: `Sacar ${carta} del mazo`, texto: "×",
      onclick: () => { fila.remove(); actualizarTotalMazo(); dibujarMazo(leerMazo()); validarEnVivo(); },
    }),
  ]);
  fila.dataset.carta = carta;
  caja.append(fila);
}

function leerMazo() {
  const mazo = {};
  for (const fila of $("mazo-filas").children) {
    mazo[fila.dataset.carta] = numero(fila.querySelector("input").value);
  }
  return mazo;
}

function actualizarTotalMazo() {
  const mazo = leerMazo();
  const total = Object.values(mazo).reduce((a, b) => a + b, 0);
  $("mazo-total").textContent = total;
  for (const fila of $("mazo-filas").children) {
    const porcentaje = total ? (100 * mazo[fila.dataset.carta]) / total : 0;
    fila.querySelector(".barra-mazo > span").style.width = `${porcentaje}%`;
    fila.querySelector(".barra-mazo").title = `${porcentaje.toFixed(1)}% del mazo`;
  }
}

function dibujarTablaDisparo(tabla) {
  const cuerpo = $("tabla-filas");
  cuerpo.innerHTML = "";
  for (const franja of tabla) filaDeDisparo(cuerpo, franja);
}

function filaDeDisparo(cuerpo, franja) {
  const campo = (valor) => el("input", {
    type: "number", min: "1", max: "6", value: valor, oninput: validarEnVivo,
  });
  const fila = el("tr", {}, [
    el("td", {}, el("input", { type: "number", min: "0", max: "20", value: franja.pases, oninput: validarEnVivo })),
    el("td", {}, el("span", { clase: "par" }, [campo(franja.gol[0]), document.createTextNode("a"), campo(franja.gol[1])])),
    el("td", {}, el("span", { clase: "par" }, [campo(franja.ataja[0]), document.createTextNode("a"), campo(franja.ataja[1])])),
  ]);
  fila.append(el("td", {}, el("button", {
    type: "button", clase: "quitar", texto: "×", title: "Quitar franja",
    onclick: () => { fila.remove(); validarEnVivo(); },
  })));
  cuerpo.append(fila);
}

function leerTablaDisparo() {
  return [...$("tabla-filas").children].map((fila) => {
    const campos = [...fila.querySelectorAll("input")].map((i) => numero(i.value));
    return { pases: campos[0], gol: [campos[1], campos[2]], ataja: [campos[3], campos[4]] };
  });
}

function leerEditor() {
  const contras = leerContras();
  return {
    id: $("r-id").value.trim(),
    nombre: $("r-nombre").value.trim(),
    version: $("r-version").value.trim(),
    descripcion: $("r-descripcion").value.trim(),
    documento: app.borrador?.documento ?? null,
    activo: $("r-activo").checked,
    extends: app.borrador?.extends ?? null,
    mazo: leerMazo(),
    partido: {
      jugadores_minimo_por_equipo: numero($("min-jugadores").value, 2),
      goles_para_ganar: numero($("goles-ganar").value, 3),
      penales_si_marcador: [numero($("penales-0").value), numero($("penales-1").value)],
      limite_turnos: numero($("limite-turnos").value, 500),
    },
    mano: { inicial: numero($("mano-inicial").value, 6), maxima: numero($("mano-maxima").value, 6) },
    reposicion: { momento: $("rep-momento").value, quien: $("rep-quien").value },
    disparo: {
      rebote: $("disparo-rebote").checked,
      palo: $("disparo-palo").checked,
      tabla: leerTablaDisparo(),
    },
    acciones_ofensivas: seleccionadas("acciones"),
    reacciones: {
      pase: { cartas: seleccionadas("reac-pase"), contra: contras["pase"] },
      pasa_turno: { cartas: seleccionadas("reac-pasa-turno"), contra: contras["pasa-turno"] },
    },
    reglas: {
      pasa_turno_sin_respuesta: $("regla-sin-respuesta").value,
      prob_falta_por_jugador: numero($("regla-falta").value) / 100,
      reacciones_encadenables: $("regla-encadenables").checked,
    },
  };
}

function actualizarAyudas() {
  $("rep-ayuda").textContent =
    `${TEXTOS_MOMENTO[$("rep-momento").value]} Levantan ${TEXTOS_QUIEN[$("rep-quien").value]}, ` +
    `hasta ${$("mano-maxima").value} cartas en la mano.`;
  $("regla-falta-valor").textContent = `${$("regla-falta").value}%`;
}

let temporizadorValidacion = null;
function validarEnVivo() {
  actualizarAyudas();
  clearTimeout(temporizadorValidacion);
  temporizadorValidacion = setTimeout(async () => {
    try {
      const resultado = await api("/api/validar", { method: "POST", body: JSON.stringify(leerEditor()) });
      mostrarErrores(resultado.errores || []);
    } catch (error) {
      mostrarErrores([error.message]);
    }
  }, 250);
}

function mostrarErrores(errores) {
  const caja = $("errores");
  caja.hidden = errores.length === 0;
  caja.innerHTML = "";
  if (!errores.length) return;
  caja.append(el("strong", { texto: "Hay que arreglar esto antes de guardar:" }));
  caja.append(el("ul", {}, errores.map((e) => el("li", { texto: e }))));
}

function conectarEditor() {
  $("editor").addEventListener("input", (evento) => {
    if (evento.target.matches("input, select, textarea")) validarEnVivo();
  });
  $("mazo-agregar").onchange = (evento) => {
    if (!evento.target.value) return;
    const mazo = leerMazo();
    mazo[evento.target.value] = 2;
    dibujarMazo(mazo);
    validarEnVivo();
  };
  $("btn-fila-disparo").onclick = () => {
    const tabla = leerTablaDisparo();
    const ultima = tabla[tabla.length - 1] || { pases: -1, gol: [1, 1], ataja: [2, 6] };
    filaDeDisparo($("tabla-filas"), { pases: ultima.pases + 1, gol: ultima.gol, ataja: ultima.ataja });
    validarEnVivo();
  };
  $("btn-guardar").onclick = () => guardarReglamento();
  $("btn-descartar").onclick = () => cargarReglamento(app.reglamentoActual);
  $("btn-duplicar").onclick = () => {
    const copia = leerEditor();
    copia.id = `${copia.id}-copia`;
    copia.nombre = `${copia.nombre} (copia)`;
    copia.extends = null;
    copia.activo = false;
    app.borrador = { ...copia, documento: null };
    app.reglamentoActual = null;
    poblarEditor(app.borrador);
    avisar("Copia lista: cambiale el id y guardala");
  };
  $("btn-borrar").onclick = async () => {
    const id = $("r-id").value.trim();
    if (!confirm(`¿Borrar el reglamento ${id}? Se elimina el archivo reglamentos/${id}.json.`)) return;
    try {
      await api(`/api/reglamentos/${encodeURIComponent(id)}`, { method: "DELETE" });
      await refrescarCatalogo();
      const primero = app.opciones.reglamentos[0];
      if (primero) await cargarReglamento(primero.id);
      avisar(`Borrado ${id}`);
    } catch (error) {
      avisar(error.message, true);
    }
  };
  $("btn-simular-este").onclick = async () => {
    const guardado = await guardarReglamento();
    if (!guardado) return;
    mostrarVista("simular");
    const primerSelect = document.querySelector("#escenarios select.selector-reglamento");
    if (primerSelect) primerSelect.value = guardado;
    correrSimulacion();
  };
}

async function guardarReglamento() {
  const datos = leerEditor();
  try {
    const respuesta = await api("/api/reglamentos", { method: "POST", body: JSON.stringify(datos) });
    await refrescarCatalogo();
    app.reglamentoActual = respuesta.guardado;
    await cargarReglamento(respuesta.guardado);
    $("estado-editor").textContent = `guardado en ${respuesta.archivo}`;
    avisar(`Guardado ${respuesta.guardado}`);
    return respuesta.guardado;
  } catch (error) {
    avisar(error.message, true);
    mostrarErrores(error.message.split("\n").map((l) => l.replace(/^\s*-\s*/, "")).slice(1));
    return null;
  }
}

// ── simulación ──────────────────────────────────────────────────────────

function agregarEscenario(indice = 0) {
  const reglamentosActivos = app.opciones.reglamentos.filter((r) => r.activo);
  const porDefecto = reglamentosActivos[indice] || app.opciones.reglamentos[indice] || app.opciones.reglamentos[0];
  const selectReglamento = el("select", { clase: "selector-reglamento" });
  opcionesSelect(selectReglamento, app.opciones.reglamentos.map((r) => r.id));
  if (porDefecto) selectReglamento.value = porDefecto.id;

  const selectPerfil = el("select", {});
  opcionesSelect(selectPerfil, app.opciones.perfiles.map((p) => p.id),
    Object.fromEntries(app.opciones.perfiles.map((p) => [p.id, p.nombre])));
  selectPerfil.value = "estrategica";

  const fila = el("div", { clase: "escenario" }, [
    el("label", { texto: "Reglamento" }, selectReglamento),
    el("label", { texto: "Jugadores por equipo" }, el("input", { type: "number", min: "2", max: "11", value: "3" })),
    el("label", { texto: "Estilo de juego" }, selectPerfil),
    el("button", { type: "button", clase: "quitar", texto: "×", title: "Quitar escenario", onclick: () => fila.remove() }),
  ]);
  $("escenarios").append(fila);
}

function leerEscenarios() {
  return [...$("escenarios").children].map((fila) => {
    const [reglamento, formato, perfil] = fila.querySelectorAll("select, input");
    return {
      reglamento: reglamento.value,
      jugadores_por_equipo: numero(formato.value, 3),
      perfil: perfil.value,
    };
  });
}

function conectarSimulacion() {
  $("btn-escenario").onclick = () => agregarEscenario($("escenarios").children.length);
  $("btn-correr").onclick = correrSimulacion;
}

async function correrSimulacion() {
  const escenarios = leerEscenarios();
  if (!escenarios.length) return avisar("Agregá al menos un escenario", true);
  const partidos = numero($("partidos").value, 200);
  $("estado-simulacion").textContent = `simulando ${escenarios.length * partidos} partidos…`;
  $("btn-correr").disabled = true;
  try {
    const datos = await api("/api/simular", {
      method: "POST",
      body: JSON.stringify({ escenarios, partidos }),
    });
    dibujarResultados(datos.resultados, partidos);
    $("estado-simulacion").textContent = "listo";
  } catch (error) {
    $("estado-simulacion").textContent = "";
    avisar(error.message, true);
  } finally {
    $("btn-correr").disabled = false;
  }
}

function dibujarResultados(resultados, partidos) {
  const caja = $("resultados");
  caja.innerHTML = "";
  if (!resultados.length) return;

  if (resultados.length === 1) caja.append(tarjetas(resultados[0]));

  const panel = el("div", { clase: "panel" });
  panel.append(el("h2", { texto: "Comparación" }));
  panel.append(el("p", { clase: "ayuda", texto: `${partidos} partidos por escenario, con las mismas semillas en todos.` }));
  panel.append(grafico("Partidos que se definen", "cuántos terminan antes del límite de turnos", resultados,
    (r) => r.pct_completados, (v) => `${v.toFixed(1)}%`, 100));
  panel.append(grafico("Goles por partido", "", resultados,
    (r) => r.goles_promedio, (v) => v.toFixed(2)));
  panel.append(grafico("Turnos por partido", "cuánto dura la partida", resultados,
    (r) => r.turnos_promedio, (v) => v.toFixed(0)));
  panel.append(grafico("Definidos por penales", "empate en el marcador de penales", resultados,
    (r) => r.pct_penales, (v) => `${v.toFixed(1)}%`, 100));
  caja.append(panel);

  const panelAcciones = el("div", { clase: "panel" });
  panelAcciones.append(el("h2", { texto: "En qué se va el juego" }));
  panelAcciones.append(el("p", { clase: "ayuda", texto: "Reparto de las acciones de cada partido." }));
  for (const resultado of resultados) panelAcciones.append(barraApilada(resultado));
  panelAcciones.append(leyendaAcciones());
  caja.append(panelAcciones);

  const panelTrampas = el("div", { clase: "panel" });
  panelTrampas.append(el("h2", { texto: "Trampa de offside y marca personal" }));
  panelTrampas.append(el("p", { clase: "ayuda", texto: "Veces por partido. Una marca puede recuperar la pelota o, más seguido, obligar al ataque a buscar otro receptor." }));
  panelTrampas.append(grafico("Trampas de offside puestas", "", resultados, (r) => r.por_partido.trampa_colocada, (v) => v.toFixed(1)));
  panelTrampas.append(grafico("Offsides cobrados", "", resultados, (r) => r.por_partido.offside_efectivo, (v) => v.toFixed(1)));
  panelTrampas.append(grafico("Marcas personales puestas", "", resultados, (r) => r.por_partido.marca_colocada, (v) => v.toFixed(1)));
  panelTrampas.append(grafico("Marcas que recuperaron la pelota", "", resultados, (r) => r.por_partido.marca_efectiva, (v) => v.toFixed(1)));
  panelTrampas.append(grafico("Pases desviados por una marca", "", resultados, (r) => r.por_partido.marca_evitada, (v) => v.toFixed(1)));
  caja.append(panelTrampas);

  caja.append(tablaResultados(resultados));
}

function tarjetas(resultado) {
  const datos = [
    ["Partidos definidos", `${resultado.pct_completados}%`, "terminaron antes del límite"],
    ["Goles por partido", resultado.goles_promedio, ""],
    ["Turnos por partido", resultado.turnos_promedio, ""],
    ["Definidos por penales", `${resultado.pct_penales}%`, ""],
  ];
  return el("div", { clase: "tarjetas" }, datos.map(([etiqueta, valor, pie]) =>
    el("div", { clase: "tarjeta" }, [
      el("div", { clase: "etiqueta", texto: etiqueta }),
      el("div", { clase: "numero", texto: String(valor) }),
      el("div", { clase: "pie", texto: pie }),
    ])));
}

function grafico(titulo, subtitulo, resultados, valorDe, formato, maximoFijo = null) {
  const valores = resultados.map(valorDe);
  const maximo = maximoFijo ?? Math.max(...valores, 0.001);
  const filas = resultados.map((resultado, i) => {
    const ancho = maximo ? Math.max(1, (100 * valores[i]) / maximo) : 0;
    return el("div", { clase: "barra-fila" }, [
      el("span", { texto: resultado.escenario.etiqueta }),
      el("div", { clase: "pista", title: `${resultado.escenario.etiqueta}: ${formato(valores[i])}` },
        el("div", { clase: "valor-barra", style: `width:${ancho}%` })),
      el("span", { clase: "cifra", texto: formato(valores[i]) }),
    ]);
  });
  return el("div", { clase: "grafico" }, [
    el("h3", { texto: titulo }),
    subtitulo ? el("p", { clase: "subtitulo", texto: subtitulo }) : null,
    el("div", { clase: "barras" }, filas),
  ]);
}

function barraApilada(resultado) {
  const reparto = resultado.reparto_acciones;
  const segmentos = ACCIONES_REPARTO.map((accion, i) => {
    const valor = reparto[accion] || 0;
    if (!valor) return null;
    return el("span", {
      style: `width:${valor}%;background:var(${SERIES[i]})`,
      title: `${app.opciones.etiquetas[accion] || accion}: ${valor}%`,
    });
  }).filter(Boolean);
  return el("div", { clase: "grafico" }, [
    el("h3", { texto: resultado.escenario.etiqueta }),
    el("div", { clase: "apilada" }, segmentos),
    el("p", { clase: "subtitulo", texto: ACCIONES_REPARTO
      .filter((a) => reparto[a])
      .map((a) => `${app.opciones.etiquetas[a] || a} ${reparto[a]}%`)
      .join(" · ") }),
  ]);
}

function leyendaAcciones() {
  return el("div", { clase: "leyenda" }, ACCIONES_REPARTO.map((accion, i) =>
    el("span", {}, [
      el("i", { style: `background:var(${SERIES[i]})` }),
      document.createTextNode(app.opciones.etiquetas[accion] || accion),
    ])));
}

function tablaResultados(resultados) {
  const columnas = [
    ["Escenario", (r) => r.escenario.etiqueta],
    ["Definidos", (r) => `${r.pct_completados}%`],
    ["Goles", (r) => r.goles_promedio],
    ["Turnos", (r) => r.turnos_promedio],
    ["Penales", (r) => `${r.pct_penales}%`],
    ["Pase %", (r) => r.reparto_acciones.pase],
    ["Robo %", (r) => r.reparto_acciones.robo],
    ["Disparo %", (r) => r.reparto_acciones.disparo],
    ["Trampas", (r) => r.por_partido.trampa_colocada],
    ["Marcas", (r) => r.por_partido.marca_colocada],
    ["Marcas OK", (r) => r.por_partido.marca_efectiva],
    ["Victorias 1 / 2", (r) => `${r.victorias[0]} / ${r.victorias[1]}`],
  ];
  const tabla = el("table", { clase: "datos" });
  tabla.append(el("thead", {}, el("tr", {}, columnas.map(([titulo]) => el("th", { texto: titulo })))));
  tabla.append(el("tbody", {}, resultados.map((r) =>
    el("tr", {}, columnas.map(([, valor], i) => el(i === 0 ? "th" : "td", { texto: String(valor(r)) }))))));
  return el("div", { clase: "panel" }, [
    el("h2", { texto: "Todos los números" }),
    el("div", { clase: "desplaza" }, tabla),
  ]);
}

// ── ver un partido ──────────────────────────────────────────────────────

function conectarPartido() {
  opcionesSelect($("p-reglamento"), app.opciones.reglamentos.map((r) => r.id));
  $("p-reglamento").classList.add("selector-reglamento");
  const activo = app.opciones.reglamentos.find((r) => r.activo);
  if (activo) $("p-reglamento").value = activo.id;
  opcionesSelect($("p-perfil"), app.opciones.perfiles.map((p) => p.id),
    Object.fromEntries(app.opciones.perfiles.map((p) => [p.id, p.nombre])));
  $("p-perfil").value = "estrategica";

  $("btn-jugar").onclick = jugarPartido;
  $("btn-reproducir").onclick = () => { pausar(); reproducir(); };
  $("btn-pausar").onclick = pausar;
  $("btn-paso").onclick = () => { pausar(); pasoRelato(); };
  $("btn-reiniciar").onclick = () => { pausar(); app.reproduccion.indice = 0; $("relato").innerHTML = ""; };
  $("ver-detalles").onchange = () => { pausar(); app.reproduccion.indice = 0; $("relato").innerHTML = ""; };
}

async function jugarPartido() {
  const nombres = $("p-nombres").value.split(",").map((n) => n.trim()).filter(Boolean);
  const cuerpo = {
    escenario: {
      reglamento: $("p-reglamento").value,
      jugadores_por_equipo: numero($("p-formato").value, 3),
      perfil: $("p-perfil").value,
    },
    semilla: $("p-semilla").value.trim(),
    nombres: nombres.length ? nombres : null,
  };
  $("estado-partido").textContent = "jugando…";
  try {
    app.partido = await api("/api/partido", { method: "POST", body: JSON.stringify(cuerpo) });
    $("estado-partido").textContent = "";
    $("panel-relato").hidden = false;
    $("p-semilla").value = app.partido.semilla ?? "";
    $("pl-equipo1").textContent = app.partido.equipos[0].join(", ");
    $("pl-equipo2").textContent = app.partido.equipos[1].join(", ");
    $("pl-marcador").textContent = "0 – 0";
    $("resumen-partido").textContent =
      `Final ${app.partido.marcador_final.join(" – ")} en ${app.partido.turnos} turnos` +
      (app.partido.definido_por_penales ? ", definido por penales." : ".") +
      ` Semilla ${app.partido.semilla}: con ese número el partido se repite igual.`;
    app.reproduccion.indice = 0;
    $("relato").innerHTML = "";
    reproducir();
  } catch (error) {
    $("estado-partido").textContent = "";
    avisar(error.message, true);
  }
}

function eventosVisibles() {
  if (!app.partido) return [];
  return $("ver-detalles").checked
    ? app.partido.eventos
    : app.partido.eventos.filter((ev) => ev.nivel === "clave");
}

function pasoRelato() {
  const eventos = eventosVisibles();
  const { indice } = app.reproduccion;
  if (indice >= eventos.length) return false;
  const evento = eventos[indice];
  const relato = $("relato");
  relato.querySelector(".actual")?.classList.remove("actual");
  relato.append(el("li", { clase: `${evento.nivel} ${evento.tipo} actual`, texto: evento.texto }));
  relato.scrollTop = relato.scrollHeight;
  $("pl-marcador").textContent = `${evento.marcador[0]} – ${evento.marcador[1]}`;
  app.reproduccion.indice += 1;
  return true;
}

function reproducir() {
  if (!pasoRelato()) return;
  app.reproduccion.temporizador = setTimeout(reproducir, ESPERAS[numero($("velocidad").value, 4) - 1]);
}

function pausar() {
  clearTimeout(app.reproduccion.temporizador);
  app.reproduccion.temporizador = null;
}

iniciar();
