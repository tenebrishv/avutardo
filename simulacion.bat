@echo off
rem Abre la pantalla de la GCS con datos simulados (prototipo de la issue #7).
rem Doble clic, o desde una terminal: simulacion.bat [variante]   (por defecto G2)
rem Teclas: <- y -> cambian de variante, F11 pantalla completa, F12 captura,
rem         F6 pendrive, F7 enlace, F8 adelanta 30 s de vuelo.
setlocal
set "VARIANTE=%~1"
if "%VARIANTE%"=="" set "VARIANTE=G2"
cd /d "%~dp0gcs"
uv run --with segno python prototipos\pantalla.py %VARIANTE%
if errorlevel 1 pause
