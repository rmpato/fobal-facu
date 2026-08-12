#!/bin/sh
# Deja el simulador listo para usar en macOS o Linux (sirve en zsh, bash o sh).
#
#   ./instalar.sh          comprueba todo y explica cómo seguir
#   ./instalar.sh --web    además abre la interfaz al terminar
#
# El simulador no usa bibliotecas externas: lo único que hace falta es Python
# 3.11 o más nuevo. Este script se asegura de que esté y de que todo funcione.

set -eu

VERSION_MINIMA_TEXTO="3.11"

rojo() { printf '\033[0;31m%s\033[0m\n' "$1"; }
verde() { printf '\033[0;32m%s\033[0m\n' "$1"; }
titulo() { printf '\n\033[1m%s\033[0m\n' "$1"; }

titulo "Fobal Facu · instalación"

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
    rojo "No se encontró Python $VERSION_MINIMA_TEXTO o más nuevo."
    echo
    echo "Para instalarlo:"
    if [ "$(uname -s)" = "Darwin" ]; then
        echo "  macOS con Homebrew:   brew install python"
        echo "  o descargarlo de:     https://www.python.org/downloads/"
    else
        echo "  Debian o Ubuntu:      sudo apt install python3"
        echo "  Fedora:               sudo dnf install python3"
        echo "  Arch:                 sudo pacman -S python"
        echo "  o descargarlo de:     https://www.python.org/downloads/"
    fi
    echo
    echo "Después volvé a correr ./instalar.sh"
    exit 1
fi

verde "Python encontrado: $("$PYTHON" --version) ($(command -v "$PYTHON"))"

# 2. Dependencias -----------------------------------------------------------
echo "Dependencias que instalar: ninguna. El simulador usa solo la biblioteca"
echo "estándar de Python, así que no hace falta pip, ni entornos virtuales."

# 3. Comprobar que ande de verdad -------------------------------------------
titulo "Comprobando que todo funcione"
cd "$(dirname "$0")"
if "$PYTHON" -m unittest discover -q >/dev/null 2>&1; then
    verde "Las 80 pruebas pasan."
else
    rojo "Las pruebas fallaron. Detalle:"
    "$PYTHON" -m unittest discover
    exit 1
fi

if "$PYTHON" -m simulador simular v2 --partidos 5 >/dev/null 2>&1; then
    verde "El simulador corre partidos correctamente."
else
    rojo "El simulador no pudo correr. Detalle:"
    "$PYTHON" -m simulador simular v2 --partidos 5
    exit 1
fi

# 4. Cómo seguir ------------------------------------------------------------
titulo "Listo. Para usarlo:"
cat <<FIN
  $PYTHON -m simulador web
      Abre la interfaz en http://localhost:8000 para editar las reglas,
      correr simulaciones y mirar un partido.

  $PYTHON -m simulador comparar v1 v2 --partidos 500
      Compara dos versiones del juego en la terminal.

  $PYTHON -m simulador ver v2
      Muestra un partido, jugada por jugada.

  $PYTHON -m simulador --help
      Todos los comandos.

Documentación: README.md y la carpeta docs/
FIN

if [ "${1:-}" = "--web" ]; then
    titulo "Abriendo la interfaz (Ctrl+C para cerrar)"
    exec "$PYTHON" -m simulador web
fi
