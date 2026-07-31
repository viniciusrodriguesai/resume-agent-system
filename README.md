# Resume Match AI V5

Plataforma local e open source para comparar currículo e vaga com **agentes tipados, privacidade antes dos embeddings, evidências por requisito, pontuação explicável, FastAPI, Streamlit, testes e fallback offline**.

## O que foi implementado

- núcleo Python desacoplado do frontend;
- modelos Pydantic para entradas, perfis, evidências, pontuação e relatórios;
- perfis `demo`, `balanced` e `complete`;
- MiniLM/E5 em ONNX quando instalados e TF-IDF + RapidFuzz como fallback;
- reranker opcional aplicado somente aos melhores candidatos;
- anonimização pt-BR antes de embeddings, cache e logs;
- upload seguro de PDF, DOCX e TXT com limite de 10 MB e validação de assinatura;
- parsing com pypdf/python-docx e Docling opcional;
- cache local por hash e histórico SQLite sem documentos brutos;
- interface Streamlit com gráficos Plotly e exportação Markdown/JSON/CSV;
- API FastAPI com `/health`, `/v1/analyze`, `/v1/profiles` e `/metrics`;
- Docker, Compose, GitHub Actions, Dependabot, Ruff, mypy, pytest e pip-audit;
- testes opcionais de acessibilidade com Playwright + axe-core.

## Instalação recomendada no seu notebook

```powershell
cd C:/Users/vinic/resume-agent-system
py -3.11 -m venv .venv
./.venv/Scripts/Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements-ai.txt
python scripts\preload_models.py --profile demo
python -m streamlit run app.py
```

Ou execute `install_demo.bat` e depois `run_demo.bat`.

## API local

```powershell
./.venv/Scripts/Activate.ps1
python -m uvicorn api.main:app --reload
```

Documentação automática: `http://127.0.0.1:8000/docs`.

## Testes

```powershell
python -m pip install -r requirements-dev.txt
python -m pytest
python -m ruff check .
python -m pip_audit -r requirements.txt
```

## Perfis

| Perfil | Modelo | Reranker | Parser avançado | Uso |
|---|---|---|---|---|
| Demo | MiniLM ONNX | Não | Não | apresentação e CPU |
| Balanced | E5-small ONNX | top 3 | Não | qualidade e velocidade |
| Complete | BGE-M3 | BGE | Docling + Presidio | máquina mais forte |

## Privacidade

O currículo é anonimizado antes da busca semântica. O histórico guarda somente metadados, nota e tempos. Nenhum texto bruto é enviado para APIs externas.

## Limitação

A ferramenta apoia revisão humana. Ela não deve selecionar, rejeitar ou classificar pessoas automaticamente sem supervisão e validação de viés.
