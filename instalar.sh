#!/bin/sh
# Deja todo listo para usar el simulador en macOS o Linux (zsh, bash o sh).
#
#   ./instalar.sh          instala lo que falte y explica como seguir
#   ./instalar.sh --web    ademas abre la interfaz grafica
#   ./instalar.sh --ver    ademas muestra un partido en la terminal
#
# El simulador anda solo con Python. Las dos bibliotecas que instala este
# script (rich y textual) son opcionales: hacen que mirar un partido en la
# terminal se vea mucho mejor.

set -eu

cd "$(dirname "$0")"

rojo() { printf '\033[0;31m%s\033[0m\n' "$1"; }
verde() { printf '\033[0;32m%s\033[0m\n' "$1"; }
titulo() { printf '\n\033[1m%s\033[0m\n' "$1"; }

titulo "Fobal Facu · instalacion"

# 1. Buscar un Python que sirva --------------------------------------------
PYTHON=""
for candidato in python3 python3.14 python3.13 python3.12 python3.11 python; do
    if command -v "$candidato" >/dev/null 2>&1; then
        if "$candidato" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)' 2>/dev/null; then
            PYTHON="$candidato"
            break
        fi
    fi
done

if [ -z "$PYTHON" ]; then
    rojo "No se encontro Python 3.11 o mas nuevo."
    echo
    echo "Para instalarlo:"
    if [ "$(uname -s)" = "Darwin" ]; then
        echo "  macOS con Homebrew:   brew install python"
        echo "  o descargalo de:      https://www.python.org/downloads/"
    else
        echo "  Debian o Ubuntu:      sudo apt install python3 python3-venv"
        echo "  Fedora:               sudo dnf install python3"
        echo "  Arch:                 sudo pacman -S python"
        echo "  o descargalo de:      https://www.python.org/downloads/"
    fi
    echo
    echo "Despues volve a correr ./instalar.sh"
    exit 1
fi

verde "Python encontrado: $("$PYTHON" --version)"

# 2. Entorno propio con las bibliotecas opcionales --------------------------
# Se instalan dentro de .venv, en esta misma carpeta: no se toca nada del
# sistema y se puede borrar con  rm -rf .venv
titulo "Bibliotecas para ver los partidos"

if [ ! -d .venv ]; then
    echo "Creando el entorno .venv ..."
    if ! "$PYTHON" -m venv .venv 2>/dev/null; then
        rojo "No se pudo crear el entorno .venv."
        echo "En Debian o Ubuntu suele faltar un paquete:  sudo apt install python3-venv"
        echo "Igual podes usar el simulador con:  $PYTHON -m simulador web"
        exit 1
    fi
fi

VENV_PYTHON=".venv/bin/python"
if "$VENV_PYTHON" -c "import rich, textual" 2>/dev/null; then
    verde "rich y textual ya estaban instalados."
else
    echo "Instalando rich y textual (una sola vez)..."
    "$VENV_PYTHON" -m pip install --quiet --upgrade pip >/dev/null 2>&1 || true
    if "$VENV_PYTHON" -m pip install --quiet rich textual; then
        verde "rich y textual instalados."
    else
        rojo "No se pudieron instalar. El simulador funciona igual, con paneles mas basicos."
    fi
fi

# 3. Comprobar que ande de verdad -------------------------------------------
titulo "Comprobando que todo funcione"
if "$VENV_PYTHON" -m simulador run --reglamento v2 --partidos 5 >/dev/null 2>&1; then
    verde "El simulador corre partidos correctamente."
else
    rojo "El simulador no pudo correr. Detalle:"
    "$VENV_PYTHON" -m simulador run --reglamento v2 --partidos 5
    exit 1
fi

# 4. Como seguir ------------------------------------------------------------
titulo "Listo. Para usarlo:"
cat <<FIN
  .venv/bin/python -m simulador web
      Abre la interfaz en el navegador: armar los equipos, editar las reglas,
      correr simulaciones y mirar un partido con la mano de cada jugador.

  .venv/bin/python -m simulador ver --reglamento v2
      El partido en la terminal, jugada por jugada.
      Espacio avanza · +/- la velocidad · Q sale.

  .venv/bin/python -m simulador compare-formatos --partidos 300
      Comparar las versiones del juego en 3v3 y 4v4.

Todo esto tambien esta en el README.
FIN

case "${1:-}" in
    --web)
        titulo "Abriendo la interfaz (Ctrl+C para cerrar)"
        exec "$VENV_PYTHON" -m simulador web
        ;;
    --ver)
        titulo "Un partido en la terminal (Q para salir)"
        exec "$VENV_PYTHON" -m simulador ver --reglamento v2
        ;;
esac
