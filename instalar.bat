@echo off
REM Deja el simulador listo para usar en Windows.
REM
REM   instalar.bat          comprueba todo y explica como seguir
REM   instalar.bat --web    ademas abre la interfaz al terminar
REM
REM El simulador no usa bibliotecas externas: lo unico que hace falta es Python
REM 3.11 o mas nuevo. Este script se asegura de que este y de que todo funcione.

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

REM 2. Dependencias
echo.
echo Dependencias que instalar: ninguna. El simulador usa solo la biblioteca
echo estandar de Python, asi que no hace falta pip, ni entornos virtuales.

REM 3. Comprobar que ande de verdad
echo.
echo == Comprobando que todo funcione ==
%PYTHON% -m unittest discover -q >nul 2>&1
if errorlevel 1 (
    echo Las pruebas fallaron. Detalle:
    %PYTHON% -m unittest discover
    exit /b 1
)
echo Las 80 pruebas pasan.

%PYTHON% -m simulador simular v2 --partidos 5 >nul 2>&1
if errorlevel 1 (
    echo El simulador no pudo correr. Detalle:
    %PYTHON% -m simulador simular v2 --partidos 5
    exit /b 1
)
echo El simulador corre partidos correctamente.

REM 4. Como seguir
echo.
echo == Listo. Para usarlo: ==
echo.
echo   %PYTHON% -m simulador web
echo       Abre la interfaz en http://localhost:8000 para editar las reglas,
echo       correr simulaciones y mirar un partido.
echo.
echo   %PYTHON% -m simulador comparar v1 v2 --partidos 500
echo       Compara dos versiones del juego en la terminal.
echo.
echo   %PYTHON% -m simulador ver v2
echo       Muestra un partido, jugada por jugada.
echo.
echo   %PYTHON% -m simulador --help
echo       Todos los comandos.
echo.
echo Documentacion: README.md y la carpeta docs\
echo.

if "%~1"=="--web" (
    echo == Abriendo la interfaz ^(Ctrl+C para cerrar^) ==
    %PYTHON% -m simulador web
)

endlocal
