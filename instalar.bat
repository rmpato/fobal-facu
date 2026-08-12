@echo off
REM Deja todo listo para usar el simulador en Windows.
REM
REM   instalar.bat          instala lo que falte y explica como seguir
REM   instalar.bat --web    ademas abre la interfaz grafica
REM   instalar.bat --ver    ademas muestra un partido en la terminal
REM
REM El simulador anda solo con Python. Las dos bibliotecas que instala este
REM script (rich y textual) son opcionales, pero en Windows conviene tenerlas:
REM sin ellas el modo espectador queda muy basico.

setlocal
cd /d "%~dp0"

echo.
echo == Fobal Facu . instalacion ==
echo.

REM 1. Buscar un Python que sirva
set PYTHON=
for %%P in ("py -3" "python" "python3") do (
    if not defined PYTHON (
        %%~P -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)" >nul 2>&1
        if not errorlevel 1 set PYTHON=%%~P
    )
)

if not defined PYTHON (
    echo No se encontro Python 3.11 o mas nuevo.
    echo.
    echo Para instalarlo:
    echo   - Desde la Microsoft Store: buscar "Python 3"
    echo   - O descargarlo de https://www.python.org/downloads/
    echo     ^(marcar "Add Python to PATH" durante la instalacion^)
    echo.
    echo Despues volve a correr instalar.bat
    exit /b 1
)

for /f "delims=" %%V in ('%PYTHON% --version') do echo Python encontrado: %%V

REM 2. Entorno propio con las bibliotecas opcionales
echo.
echo == Bibliotecas para ver los partidos ==
if not exist ".venv\Scripts\python.exe" (
    echo Creando el entorno .venv ...
    %PYTHON% -m venv .venv
    if errorlevel 1 (
        echo No se pudo crear el entorno .venv.
        echo Igual podes usar el simulador con:  %PYTHON% -m simulador web
        exit /b 1
    )
)

set VENV=.venv\Scripts\python.exe
%VENV% -c "import rich, textual" >nul 2>&1
if errorlevel 1 (
    echo Instalando rich y textual ^(una sola vez^)...
    %VENV% -m pip install --quiet --upgrade pip >nul 2>&1
    %VENV% -m pip install --quiet rich textual
    if errorlevel 1 (
        echo No se pudieron instalar. El simulador funciona igual, con paneles mas basicos.
    ) else (
        echo rich y textual instalados.
    )
) else (
    echo rich y textual ya estaban instalados.
)

REM 3. Comprobar que ande de verdad
echo.
echo == Comprobando que todo funcione ==
%VENV% -m simulador run --reglamento v2 --partidos 5 >nul 2>&1
if errorlevel 1 (
    echo El simulador no pudo correr. Detalle:
    %VENV% -m simulador run --reglamento v2 --partidos 5
    exit /b 1
)
echo El simulador corre partidos correctamente.

REM 4. Como seguir
echo.
echo == Listo. Para usarlo: ==
echo.
echo   .venv\Scripts\python -m simulador web
echo       Abre la interfaz en el navegador: armar los equipos, editar las
echo       reglas, correr simulaciones y mirar un partido.
echo.
echo   .venv\Scripts\python -m simulador ver --reglamento v2 --ui textual
echo       El partido en la terminal, jugada por jugada.
echo       Espacio avanza . +/- la velocidad . Q sale.
echo.
echo   .venv\Scripts\python -m simulador compare-formatos --partidos 300
echo       Comparar las versiones del juego en 3v3 y 4v4.
echo.
echo En Windows conviene --ui textual: curses no viene con Python.
echo Todo esto tambien esta en el README.
echo.

if "%~1"=="--web" (
    echo == Abriendo la interfaz ^(Ctrl+C para cerrar^) ==
    %VENV% -m simulador web
)
if "%~1"=="--ver" (
    echo == Un partido en la terminal ^(Q para salir^) ==
    %VENV% -m simulador ver --reglamento v2 --ui textual
)

endlocal
