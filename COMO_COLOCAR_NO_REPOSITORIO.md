# Como colocar a V4 no seu repositório

## 1. Pare o Streamlit

No terminal do VS Code, pressione:

```text
Ctrl + C
```

## 2. Faça uma cópia de segurança

Dentro de `C:\Users\vinic`, copie a pasta `resume-agent-system` e renomeie a cópia para `resume-agent-system-backup`.

## 3. Copie os arquivos

Extraia o ZIP da V4. Entre na pasta extraída, selecione todo o conteúdo e copie para:

```text
C:\Users\vinic\resume-agent-system
```

Escolha **Substituir os arquivos no destino**. Não apague a pasta oculta `.git`.

## 4. Instale

No terminal do VS Code:

```powershell
cd C:\Users\vinic\resume-agent-system
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Para instalar a IA completa:

```powershell
python -m pip install -r requirements-full.txt
python scriptsaixar_modelos.py
python -m streamlit run app.py
```

## 5. Teste

```powershell
python -m pytest -q
```

## 6. Envie ao GitHub

```powershell
git add .
git commit -m "Upgrade resume analysis system to V4 in Portuguese"
git push
```
