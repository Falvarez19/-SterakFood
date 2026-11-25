@echo off
setlocal EnableExtensions DisableDelayedExpansion
chcp 65001 >nul
cd /d "%~dp0"
title SterakFood Desktop Local
set "PYTHON_EXE="
if exist "%~dp0.venv\Scripts\python.exe" call :TEST "%~dp0.venv\Scripts\python.exe"
if not defined PYTHON_EXE if exist "%~dp0.venv_local\Scripts\python.exe" call :TEST "%~dp0.venv_local\Scripts\python.exe"
if not defined PYTHON_EXE if exist "%~dp0venv\Scripts\python.exe" call :TEST "%~dp0venv\Scripts\python.exe"
if not defined PYTHON_EXE call :TEST python
if not defined PYTHON_EXE call :TEST py
if not defined PYTHON_EXE goto ERROR
"%PYTHON_EXE%" "%~dp0desktop6c\runner.py"
echo.
echo SterakFood Desktop finalizado.
pause
exit /b 0
:TEST
if defined PYTHON_EXE exit /b 0
%1 -c "import django,requests;import sys;assert sys.version_info >=(3,10)" >nul 2>&1
if not errorlevel 1 set "PYTHON_EXE=%~1"
exit /b 0
:ERROR
echo No se encontró Python con Django. Ejecutá primero el instalador 6C.
pause
exit /b 1
