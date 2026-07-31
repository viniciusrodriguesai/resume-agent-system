# Como instalar a V5.1 no seu repositório

## 1. Pare o Streamlit

No terminal atual, pressione `Ctrl + C`.

## 2. Faça backup

Copie a pasta atual `C:\Users\vinic\resume-agent-system` para outro local.

## 3. Substitua os arquivos

Extraia o ZIP da V5.1 e copie **todo o conteúdo interno** para:

```text
C:\Users\vinic\resume-agent-system
```

Escolha **Substituir os arquivos no destino**. Não apague a pasta oculta `.git`.

## 4. Reinicie usando o ambiente atual

A V5.1 não adiciona dependências obrigatórias. Use o ambiente que já funcionava:

```powershell
cd C:\Users\vinic\resume-agent-system
.\.venv\Scripts\Activate.ps1
python -m streamlit cache clear
python -m streamlit run app.py
```

Somente recrie o ambiente se a instalação atual estiver com erro.

## 5. Teste

```powershell
python -m pip install -r requirements-dev.txt
python -m pytest
```

## 6. Envie ao GitHub

```powershell
git add .
git commit -m "Fix evidence matching and interface in V5.1"
git push origin main
```
