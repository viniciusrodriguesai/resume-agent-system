# Como instalar no seu repositório

## 1. Pare a aplicação atual

No terminal do VS Code:

```text
Ctrl + C
```

## 2. Faça uma cópia de segurança

Dentro de `C:\Users\vinic\resume-agent-system`, execute:

```powershell
git add .
git commit -m "Backup before professional AI upgrade"
git push
```

## 3. Substitua os arquivos

Extraia o conteúdo deste pacote e copie **os arquivos internos** para:

```text
C:\Users\vinic\resume-agent-system
```

Escolha **Substituir os arquivos no destino**. Não apague a pasta oculta
`.git`.

## 4. Instalação rápida

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Essa versão já funciona com o mecanismo alternativo local.

## 5. Instalação completa de IA

```powershell
python -m pip install -r requirements-full.txt
python scripts\download_models.py
python -m streamlit run app.py
```

Também é possível clicar duas vezes em:

```text
install_full_ai.bat
```

## 6. Teste

```powershell
pytest -q
```

O resultado esperado é:

```text
3 passed
```

## 7. Envie para o GitHub

```powershell
git add .
git commit -m "Upgrade to professional local multi-agent AI system"
git push
```
