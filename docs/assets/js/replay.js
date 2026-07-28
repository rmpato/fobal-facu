/**
 * Motor de replay para FOBAL FACU (GitHub Pages + local).
 */
(function (global) {
  "use strict";

  var DELAYS = [2000, 1200, 800, 500, 350, 250, 150, 80];

  function fmt(ev) {
    var t = (ev.texto || "").trim();
    if (!t) return "";
    if (t.indexOf("T") === 0 && t.indexOf("|") !== -1) {
      return ">> " + t.replace(/^T/, "TURNO ");
    }
    if (t.indexOf("** GOL") === 0) {
      return "** " + t.replace(/^\*\*\s*/, "");
    }
    return t;
  }

  function cls(ev) {
    if (ev.tipo === "gol") return "gol";
    if (ev.tipo === "turno") return "turno";
    if (ev.tier === "detail" || ev.tier === "noise") return "dim";
    return "";
  }

  function Player(opts) {
    this.feedEl = opts.feedEl;
    this.scoreEl = opts.scoreEl;
    this.metaEl = opts.metaEl;
    this.speedEl = opts.speedEl;
    this.speedLabelEl = opts.speedLabelEl;
    this.statusEl = opts.statusEl;
    this.data = null;
    this.idx = 0;
    this.timer = null;
    this.playing = false;
  }

  Player.prototype.delay = function () {
    var v = parseInt(this.speedEl.value, 10) || 3;
    return DELAYS[Math.max(0, Math.min(DELAYS.length - 1, v - 1))];
  };

  Player.prototype.updateSpeedLabel = function () {
    var v = parseInt(this.speedEl.value, 10) || 3;
    this.speedLabelEl.textContent = ((9 - v) / 2).toFixed(1).replace(".0", "") + "x";
  };

  Player.prototype.setStatus = function (msg) {
    if (this.statusEl) this.statusEl.textContent = msg || "";
  };

  Player.prototype.setMeta = function (data) {
    if (!data) {
      this.metaEl.textContent = "Elegí un partido o cargá un JSON.";
      return;
    }
    var e0 = (data.equipos && data.equipos[0]) ? data.equipos[0].join(", ") : "?";
    var e1 = (data.equipos && data.equipos[1]) ? data.equipos[1].join(", ") : "?";
    this.metaEl.textContent =
      "Semilla #" + data.semilla + " · " + (data.reglamento || "?") + " · " + e0 + " vs " + e1;
  };

  Player.prototype.updateScore = function () {
    var s = (this.data && this.data.marcador_final) || [0, 0];
    this.scoreEl.textContent = s[0] + " - " + s[1];
  };

  Player.prototype.load = function (data) {
    this.stop();
    this.data = data;
    this.idx = 0;
    this.feedEl.innerHTML = "";
    this.setMeta(data);
    this.updateScore();
    var n = (data.eventos && data.eventos.length) || 0;
    this.setStatus(n ? n + " eventos cargados. Play para reproducir." : "Sin eventos.");
  };

  Player.prototype.render = function (to) {
    if (!this.data || !this.data.eventos) return;
    this.feedEl.innerHTML = "";
    var events = this.data.eventos;
    for (var i = 0; i <= to && i < events.length; i++) {
      var ev = events[i];
      var line = fmt(ev);
      if (!line && ev.tier === "noise") continue;
      var div = document.createElement("div");
      div.className = "replay-line " + cls(ev) + (i === to ? " active" : "");
      div.textContent = line || " ";
      this.feedEl.appendChild(div);
    }
    this.feedEl.scrollTop = this.feedEl.scrollHeight;
    this.updateScore();
  };

  Player.prototype.tick = function () {
    if (!this.data || !this.data.eventos) return;
    if (this.idx >= this.data.eventos.length) {
      this.playing = false;
      this.setStatus("Fin del replay.");
      return;
    }
    this.render(this.idx);
    this.idx++;
    var self = this;
    if (this.playing && this.idx < this.data.eventos.length) {
      this.timer = setTimeout(function () { self.tick(); }, this.delay());
    } else {
      this.playing = false;
      if (this.idx >= this.data.eventos.length) this.setStatus("Fin del replay.");
    }
  };

  Player.prototype.play = function () {
    if (!this.data) return;
    if (this.idx >= this.data.eventos.length) this.idx = 0;
    this.playing = true;
    this.setStatus("Reproduciendo…");
    this.tick();
  };

  Player.prototype.pause = function () {
    this.playing = false;
    if (this.timer) clearTimeout(this.timer);
    this.setStatus("Pausado.");
  };

  Player.prototype.step = function () {
    if (!this.data || this.idx >= this.data.eventos.length) return;
    this.pause();
    this.render(this.idx);
    this.idx++;
  };

  Player.prototype.restart = function () {
    this.pause();
    this.idx = 0;
    this.feedEl.innerHTML = "";
    this.updateScore();
    this.setStatus("Listo. Play para reproducir.");
  };

  Player.prototype.stop = function () {
    this.pause();
    this.idx = 0;
  };

  function resolveUrl(path, baseHref) {
    try {
      return new URL(path, baseHref).href;
    } catch (e) {
      return path;
    }
  }

  function fetchReplay(path, baseHref) {
    var url = resolveUrl(path, baseHref);
    return fetch(url).then(function (r) {
      if (!r.ok) throw new Error("HTTP " + r.status + " al cargar " + path);
      return r.json();
    });
  }

  function readFile(file) {
    return new Promise(function (resolve, reject) {
      var reader = new FileReader();
      reader.onload = function () {
        try {
          resolve(JSON.parse(reader.result));
        } catch (e) {
          reject(new Error("JSON inválido"));
        }
      };
      reader.onerror = function () { reject(new Error("No se pudo leer el archivo")); };
      reader.readAsText(file);
    });
  }

  global.FobalReplay = {
    Player: Player,
    fetchReplay: fetchReplay,
    readFile: readFile,
    resolveUrl: resolveUrl,
  };
})(window);
