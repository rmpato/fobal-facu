"""Grabación JSON y export HTML del modo espectador."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def escribir_grabacion(path: Path, datos: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(datos, ensure_ascii=False, indent=2), encoding="utf-8")


def exportar_html_replay(path: Path, datos: dict[str, Any]) -> Path:
    """Genera un HTML standalone junto al JSON (o en path dado)."""
    if path.suffix.lower() == ".json":
        html_path = path.with_suffix(".html")
    else:
        html_path = path
    payload = json.dumps(datos, ensure_ascii=False)
    html = _PLANTILLA_HTML.replace("__DATOS__", payload)
    html_path.write_text(html, encoding="utf-8")
    return html_path


_PLANTILLA_HTML = """<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>FOBAL FACU — Replay</title>
  <style>
    :root { --bg:#0d1117; --panel:#161b22; --text:#e6edf3; --dim:#8b949e;
            --gol:#f0c14b; --turno:#58a6ff; --border:#30363d; }
    * { box-sizing: border-box; }
    body { margin:0; font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
           background:var(--bg); color:var(--text); min-height:100vh; }
    header { padding:1rem 1.25rem; border-bottom:1px solid var(--border);
             display:flex; flex-wrap:wrap; gap:1rem; align-items:center; }
    h1 { margin:0; font-size:1.1rem; font-weight:600; }
    .meta { color:var(--dim); font-size:.85rem; }
    main { display:grid; grid-template-columns:1fr 280px; gap:1rem; padding:1rem; max-width:1200px; margin:0 auto; }
    @media (max-width:800px) { main { grid-template-columns:1fr; } }
    #feed { background:var(--panel); border:1px solid var(--border); border-radius:8px;
            height:70vh; overflow-y:auto; padding:.75rem; font-size:.9rem; line-height:1.45; }
    .line { padding:.15rem 0; white-space:pre-wrap; word-break:break-word; }
    .line.gol { color:var(--gol); font-weight:700; }
    .line.turno { color:var(--turno); font-weight:600; }
    .line.dim { color:var(--dim); }
    .line.active { background:#21262d; border-radius:4px; }
    aside { background:var(--panel); border:1px solid var(--border); border-radius:8px; padding:1rem; }
    aside h2 { margin:0 0 .75rem; font-size:.95rem; }
    .score { font-size:1.4rem; font-weight:700; margin-bottom:.5rem; }
    label { display:block; margin:.5rem 0 .25rem; font-size:.8rem; color:var(--dim); }
    input[type=range] { width:100%; }
    .btns { display:flex; flex-wrap:wrap; gap:.5rem; margin-top:.75rem; }
    button { background:#238636; color:#fff; border:none; padding:.45rem .75rem;
             border-radius:6px; cursor:pointer; font:inherit; font-size:.85rem; }
    button.secondary { background:#21262d; border:1px solid var(--border); color:var(--text); }
    button:disabled { opacity:.5; cursor:not-allowed; }
    footer { text-align:center; padding:1rem; color:var(--dim); font-size:.8rem; }
  </style>
</head>
<body>
  <header>
    <h1>FOBAL FACU — Replay</h1>
    <div class="meta" id="meta"></div>
  </header>
  <main>
    <div id="feed"></div>
    <aside>
      <h2>Controles</h2>
      <div class="score" id="score">0 - 0</div>
      <label>Velocidad (<span id="speed-label">1x</span>)</label>
      <input type="range" id="speed" min="1" max="8" value="3">
      <div class="btns">
        <button id="play">Play</button>
        <button id="pause" class="secondary">Pausa</button>
        <button id="step" class="secondary">+1</button>
        <button id="restart" class="secondary">Reiniciar</button>
      </div>
    </aside>
  </main>
  <footer>Generado por fobal-facu · <a href="https://github.com/rmpato/fobal-facu" style="color:#58a6ff">repo</a></footer>
  <script>
    const DATA = __DATOS__;
    const feed = document.getElementById("feed");
    const meta = document.getElementById("meta");
    const scoreEl = document.getElementById("score");
    meta.textContent = `Semilla #${DATA.semilla} · ${DATA.reglamento} · ${DATA.equipos?.[0]?.join(", ")} vs ${DATA.equipos?.[1]?.join(", ")}`;
    let idx = 0, timer = null, playing = false;
    const delays = [2000,1200,800,500,350,250,150,80];
    function delay() { return delays[parseInt(document.getElementById("speed").value,10)-1]; }
    document.getElementById("speed").oninput = e => {
      document.getElementById("speed-label").textContent = (9-e.target.value)/2 + "x";
    };
    function cls(ev) {
      if (ev.tipo === "gol") return "gol";
      if (ev.tipo === "turno") return "turno";
      if (ev.tier === "detail" || ev.tier === "noise") return "dim";
      return "";
    }
    function fmt(ev) {
      const t = ev.texto.trim();
      if (!t) return "";
      if (t.startsWith("T") && t.includes("|")) return ">> " + t.replace(/^T/, "TURNO ");
      if (t.startsWith("** GOL")) return "** " + t.replace(/^\\*\\*\\s*/, "");
      return t;
    }
    function updateScore() {
      const s = DATA.marcador_final || [0,0];
      scoreEl.textContent = s[0] + " - " + s[1];
    }
    function render(to) {
      feed.innerHTML = "";
      for (let i = 0; i <= to && i < DATA.eventos.length; i++) {
        const ev = DATA.eventos[i];
        const line = fmt(ev);
        if (!line && ev.tier === "noise") continue;
        const div = document.createElement("div");
        div.className = "line " + cls(ev) + (i === to ? " active" : "");
        div.textContent = line || " ";
        feed.appendChild(div);
      }
      feed.scrollTop = feed.scrollHeight;
      updateScore();
    }
    function tick() {
      if (idx >= DATA.eventos.length) { playing = false; return; }
      render(idx);
      idx++;
      if (playing && idx < DATA.eventos.length) timer = setTimeout(tick, delay());
      else playing = false;
    }
    document.getElementById("play").onclick = () => {
      if (idx >= DATA.eventos.length) idx = 0;
      playing = true; tick();
    };
    document.getElementById("pause").onclick = () => { playing = false; clearTimeout(timer); };
    document.getElementById("step").onclick = () => {
      if (idx < DATA.eventos.length) { render(idx); idx++; }
    };
    document.getElementById("restart").onclick = () => {
      playing = false; clearTimeout(timer); idx = 0; feed.innerHTML = ""; updateScore();
    };
    updateScore();
  </script>
</body>
</html>
"""
