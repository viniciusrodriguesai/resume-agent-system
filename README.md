# Resume Match AI V5.1

Plataforma local e open source para comparar currículo e vaga com **agentes tipados, privacidade antes dos embeddings, evidências por requisito, pontuação explicável, FastAPI, Streamlit, testes e fallback offline**.

## Correções da V5.1

- evidências divididas em trechos curtos e específicos;
- marcadores técnicos como `<EMAIL>` e `<NOME_CANDIDATO>` ocultos da interface e dos relatórios;
- requisitos com várias competências exigem cobertura de todas elas para receber nota alta;
- embeddings do currículo calculados uma única vez e consultas processadas em lote;
- cache de embeddings por currículo durante a sessão;
- filtros, tabelas, status e métricas traduzidos para português;
- painel de privacidade simplificado, mantendo JSON apenas em detalhes avançados;
- opção **Enviar arquivos** corrigida;
- textos introdutórios da vaga deixaram de ser classificados como requisitos;
- tempos dos agentes exibidos de forma legível;
- cache de análises versionado para não reutilizar resultados antigos da V5.

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

## Atualização rápida da V5 para a V5.1

A V5.1 não adiciona dependências obrigatórias. Depois de copiar os arquivos, basta reiniciar o Streamlit:

```powershell
cd C:/Users/vinic/resume-agent-system
./.venv/Scripts/Activate.ps1
python -m streamlit cache clear
python -m streamlit run app.py
```

O cache interno usa a versão do sistema na chave, portanto análises antigas não serão reaproveitadas.

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
