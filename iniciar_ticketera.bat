@echo off
cd /d "%~dp0"
:: Ejecuta el script de manera oculta y el .bat se cierra al instante
start "" pythonw ticketera.py
exit