@echo off
cd /d "%~dp0"
start "likSociety" conhost.exe python "%~dp0main.py"
