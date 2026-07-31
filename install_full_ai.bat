@echo off
setlocal
if not exist .venv (
    py -m venv .venv
)
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
python -m pip install -r requirements-full.txt
python scripts\download_models.py
echo Full local AI installation completed.
pause
endlocal
