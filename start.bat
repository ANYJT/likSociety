@echo off
cd /d "%~dp0"
start "" conhost.exe python "%~dp0main.py"
