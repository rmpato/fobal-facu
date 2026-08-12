"""Grabación de partidos: JSON para volver a verlos y página HTML autónoma."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from simulador.modelo import EstadoPartido

FORMATO = 2


def grabacion(estado: EstadoPartido, *, perfiles: str = "") -> dict[str, Any]:
    """Vuelca el partido entero a un diccionario serializable."""
    reg = estado.reglamento
    return {
        "formato_grabacion": FORMATO,
        "reglamento": {"id": reg.id, "nombre": reg.nombre, "version": reg.version},
        "formato": f"{estado.jugadores_por_equipo}v{estado.jugadores_por_equipo}",
        "semilla": estado.semilla,
        "perfiles": perfiles,
        "equipos": [
            [j.nombre for j in estado.equipo(0)],
            [j.nombre for j in estado.equipo(1)],
        ],
        "marcador_final": list(estado.marcador.goles),
        "turnos": estado.turno,
        "motivo_fin": estado.motivo_fin,
        "definido_por_penales": estado.definido_por_penales,
        "eventos": [e.a_dict() for e in estado.eventos],
    }


def guardar(estado: EstadoPartido, ruta: Path, *, perfiles: str = "") -> list[Path]:
    """Guarda la grabación. Con extensión ``.html`` escribe también la página."""
    datos = grabacion(estado, perfiles=perfiles)
    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    escritos = []

    json_path = ruta.with_suffix(".json")
    json_path.write_text(json.dumps(datos, ensure_ascii=False, indent=2), encoding="utf-8")
    escritos.append(json_path)

    if ruta.suffix.lower() == ".html":
        escritos.append(exportar_html(datos, ruta))
    return escritos


def exportar_html(datos: dict[str, Any], ruta: Path) -> Path:
    """Escribe una página independiente que reproduce el partido."""
    ruta = Path(ruta).with_suffix(".html")
    contenido = PLANTILLA.replace("/*DATOS*/null", json.dumps(datos, ensure_ascii=False))
    ruta.write_text(contenido, encoding="utf-8")
    return ruta


PLANTILLA = """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow">
<title>Fobal Facu — partido grabado</title>
<style>
  :root {
    color-scheme: dark;
    --fondo: #0f1115; --panel: #171a21; --borde: #262b36;
    --texto: #e6e9ef; --tenue: #98a1b3; --gol: #f5c451; --clave: #6aa9ff; --robo: #ff8a7a;
  }
  * { box-sizing: border-box; }
  body { margin: 0; background: var(--fondo); color: var(--texto);
         font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; }
  header { padding: 1rem 1.25rem; border-bottom: 1px solid var(--borde); }
  h1 { margin: 0 0 .25rem; font-size: 1.05rem; }
  .meta { color: var(--tenue); font-size: .85rem; }
  main { display: grid; grid-template-columns: 1fr 260px; gap: 1rem;
         padding: 1rem; max-width: 1100px; margin: 0 auto; }
  @media (max-width: 760px) { main { grid-template-columns: 1fr; } }
  #relato { background: var(--panel); border: 1px solid var(--borde); border-radius: 10px;
            height: 70vh; overflow-y: auto; padding: .75rem 1rem; font-size: .9rem; line-height: 1.5; }
  .linea { padding: .1rem 0; white-space: pre-wrap; }
  .linea.detalle { color: var(--tenue); }
  .linea.gol { color: var(--gol); font-weight: 700; }
  .linea.turno, .linea.fin, .linea.penales { color: var(--clave); }
  .linea.robo, .linea.offside, .linea.marca { color: var(--robo); }
  .linea.actual { background: #222735; border-radius: 5px; }
  aside { background: var(--panel); border: 1px solid var(--borde);
          border-radius: 10px; padding: 1rem; height: max-content; }
  .marcador { font-size: 1.6rem; font-weight: 700; text-align: center; margin: .25rem 0 .75rem; }
  .equipos { color: var(--tenue); font-size: .8rem; text-align: center; margin-bottom: 1rem; }
  label { display: block; font-size: .78rem; color: var(--tenue); margin: .6rem 0 .2rem; }
  input[type=range] { width: 100%; }
  .botones { display: flex; gap: .4rem; flex-wrap: wrap; margin-top: .8rem; }
  button { flex: 1; background: #2a3242; color: var(--texto); border: 1px solid var(--borde);
           border-radius: 6px; padding: .45rem .6rem; font: inherit; font-size: .85rem; cursor: pointer; }
  button.principal { background: #2f6f4f; border-color: #2f6f4f; }
  button:hover { filter: brightness(1.15); }
  footer { text-align: center; color: var(--tenue); font-size: .78rem; padding: 1rem; }
</style>
</head>
<body>
<header>
  <h1 id="titulo">Fobal Facu</h1>
  <div class="meta" id="meta"></div>
</header>
<main>
  <div id="relato"></div>
  <aside>
    <div class="marcador" id="marcador">0 - 0</div>
    <div class="equipos" id="equipos"></div>
    <label>Velocidad: <span id="etiqueta-velocidad">normal</span></label>
    <input type="range" id="velocidad" min="1" max="6" value="3">
    <label><input type="checkbox" id="detalles" checked> mostrar tiradas de dado</label>
    <div class="botones">
      <button class="principal" id="reproducir">Reproducir</button>
      <button id="pausar">Pausa</button>
    </div>
    <div class="botones">
      <button id="paso">Siguiente</button>
      <button id="reiniciar">Reiniciar</button>
    </div>
  </aside>
</main>
<footer>Partido generado con el simulador de Fobal Facu</footer>
<script>
const DATOS = /*DATOS*/null;
const relato = document.getElementById("relato");
const marcador = document.getElementById("marcador");
const velocidad = document.getElementById("velocidad");
const detalles = document.getElementById("detalles");
const ESPERAS = [1600, 1000, 600, 350, 180, 60];
const NOMBRES_VELOCIDAD = ["muy lento", "lento", "normal", "rápido", "muy rápido", "turbo"];

document.getElementById("titulo").textContent =
  `${DATOS.equipos[0].join(", ")}  vs  ${DATOS.equipos[1].join(", ")}`;
document.getElementById("meta").textContent =
  `Reglamento ${DATOS.reglamento.id} · ${DATOS.formato} · semilla ${DATOS.semilla ?? "—"}` +
  (DATOS.perfiles ? ` · ${DATOS.perfiles}` : "");
document.getElementById("equipos").textContent =
  `${DATOS.equipos[0].join(", ")} · ${DATOS.equipos[1].join(", ")}`;

let indice = 0, temporizador = null;

function visibles() {
  return DATOS.eventos.filter(ev => detalles.checked || ev.nivel === "clave");
}
function pintar(hasta) {
  const lista = visibles();
  relato.innerHTML = "";
  lista.slice(0, hasta + 1).forEach((ev, i) => {
    const div = document.createElement("div");
    div.className = `linea ${ev.nivel} ${ev.tipo}` + (i === hasta ? " actual" : "");
    div.textContent = ev.texto;
    relato.appendChild(div);
  });
  const ev = lista[Math.min(hasta, lista.length - 1)];
  if (ev) marcador.textContent = `${ev.marcador[0]} - ${ev.marcador[1]}`;
  relato.scrollTop = relato.scrollHeight;
}
function paso() {
  const lista = visibles();
  if (indice >= lista.length) return false;
  pintar(indice);
  indice++;
  return true;
}
function reproducir() {
  if (!paso()) return pausar();
  temporizador = setTimeout(reproducir, ESPERAS[velocidad.value - 1]);
}
function pausar() { clearTimeout(temporizador); temporizador = null; }

document.getElementById("reproducir").onclick = () => { pausar(); reproducir(); };
document.getElementById("pausar").onclick = pausar;
document.getElementById("paso").onclick = () => { pausar(); paso(); };
document.getElementById("reiniciar").onclick = () => {
  pausar(); indice = 0; relato.innerHTML = ""; marcador.textContent = "0 - 0";
};
velocidad.oninput = () => {
  document.getElementById("etiqueta-velocidad").textContent = NOMBRES_VELOCIDAD[velocidad.value - 1];
};
detalles.onchange = () => { indice = 0; relato.innerHTML = ""; };
pintar(0);
</script>
</body>
</html>
"""
