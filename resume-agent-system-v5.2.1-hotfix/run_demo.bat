@echo off
call .venv\Scripts\activate.bat
powershell -ExecutionPolicy Bypass -File scripts\run_demo.ps1
