# Como instalar a V5 no seu repositório

## 1. Pare o Streamlit

No terminal atual, pressione `Ctrl + C`.

## 2. Faça backup

Copie a pasta atual `C:\Users\vinic\resume-agent-system` para outro local.

## 3. Substitua os arquivos

Extraia o ZIP da V5 e copie **todo o conteúdo interno** para:

```text
C:\Users\vinic\resume-agent-system
```

Escolha **Substituir os arquivos no destino**. Não apague a pasta oculta `.git`.

## 4. Recrie o ambiente recomendado

```powershell
cd C:\Users\vinic\resume-agent-system
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements-ai.txt
python scripts\preload_models.py --profile demo
python -m streamlit run app.py
```

## 5. Teste

```powershell
python -m pip install -r requirements-dev.txt
python -m pytest
```

## 6. Envie ao GitHub

```powershell
git add .
git commit -m "Upgrade project to local professional V5"
git push origin main
```
