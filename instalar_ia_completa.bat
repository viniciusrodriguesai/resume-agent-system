@echo off
setlocal
if not exist .venv py -m venv .venv
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
python -m pip install -r requirements-full.txt
python -m spacy download en_core_web_sm
python scripts\baixar_modelos.py
python -m streamlit run app.py
endlocal
