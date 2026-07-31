@echo off
call .venv\Scripts\activate.bat
powershell -ExecutionPolicy Bypass -File scripts\run_api.ps1
