<div align="center">

# Resume Match AI V5

### Análise local, explicável e multiagente de currículos e vagas

Compare requisitos, encontre evidências no currículo, identifique lacunas e gere recomendações — sem enviar documentos para APIs externas.

[![CI](https://github.com/viniciusrodriguesai/resume-agent-system/actions/workflows/ci.yml/badge.svg)](https://github.com/viniciusrodriguesai/resume-agent-system/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![FastAPI](https://img.shields.io/badge/API-FastAPI-009688?logo=fastapi&logoColor=white)](http://127.0.0.1:8000/docs)
[![Streamlit](https://img.shields.io/badge/UI-Streamlit-FF4B4B?logo=streamlit&logoColor=white)](http://localhost:8501)
[![Local First](https://img.shields.io/badge/AI-local--first-6C63FF)](#privacidade-e-segurança)

[Visão geral](#visão-geral) ·
[Instalação](#início-rápido) ·
[Arquitetura](#arquitetura) ·
[API](#api-local) ·
[Segurança](#privacidade-e-segurança)

</div>

---

## Visão geral

O **Resume Match AI V5** é uma plataforma open source para comparar currículos e descrições de vagas com uma abordagem **local-first**, **explicável** e **multiagente**.

Em vez de retornar apenas uma porcentagem, o sistema mostra:

- quais requisitos foram encontrados;
- quais requisitos estão parcialmente atendidos;
- quais requisitos estão ausentes;
- qual trecho do currículo sustenta cada conclusão;
- como a pontuação foi calculada;
- quais melhorias podem ser feitas sem inventar experiências.

> [!IMPORTANT]
> A ferramenta oferece apoio à análise humana. Ela não deve selecionar, rejeitar ou classificar candidatos automaticamente sem supervisão, validação de viés e contexto adequado.

## Por que este projeto?

Comparadores tradicionais dependem de palavras exatas. Isso pode falhar quando currículo e vaga descrevem a mesma competência com termos diferentes.

Exemplo:

```text
Vaga: "experiência com modelagem preditiva"
Currículo: "desenvolvimento de modelos de machine learning"
```

O Resume Match AI combina regras, busca lexical, similaridade semântica e reranqueamento opcional para encontrar relações como essa e apresentar a evidência utilizada.

## Principais recursos

### Inteligência e agentes

- pipeline multiagente com responsabilidades separadas;
- modelos Pydantic para entradas, perfis, evidências, notas e relatórios;
- busca lexical com TF-IDF e RapidFuzz;
- embeddings locais opcionais;
- reranker opcional aplicado apenas aos melhores candidatos;
- revisão automática de casos limítrofes;
- recomendações priorizadas e baseadas em evidências;
- fallback offline quando os modelos de IA não estão disponíveis.

### Privacidade

- anonimização antes dos embeddings, cache e análise;
- remoção de e-mail, telefone, CPF, CNPJ, CEP, URLs e outros identificadores;
- histórico SQLite sem armazenar currículo ou vaga em texto bruto;
- nenhuma dependência obrigatória de API externa;
- chave opcional para proteger a API local.

### Documentos e relatórios

- entrada por texto ou upload;
- suporte a PDF, DOCX e TXT;
- limite de upload de 10 MB;
- validação de assinatura e estrutura dos arquivos;
- parsing leve com `pypdf` e `python-docx`;
- Docling opcional para documentos complexos;
- exportação em Markdown, JSON e CSV.

### Engenharia

- frontend em Streamlit;
- API REST em FastAPI;
- núcleo desacoplado das interfaces;
- Docker e Docker Compose;
- testes com pytest;
- lint com Ruff;
- tipagem com mypy;
- auditoria de dependências com pip-audit;
- integração contínua com GitHub Actions;
- Dependabot para atualizações de dependências.

## Como funciona

```text
Currículo + vaga
      │
      ▼
Agente de privacidade
      │
      ▼
Agentes de estruturação
      │
      ├── perfil do candidato
      └── requisitos da vaga
      │
      ▼
Motor de evidências
      ├── TF-IDF
      ├── RapidFuzz
      ├── embeddings opcionais
      └── reranker opcional
      │
      ▼
Pontuação explicável
      │
      ▼
Agente revisor
      │
      ├── revisão necessária ──► nova análise
      └── aprovado
      │
      ▼
Recomendações + relatórios
```

A aplicação Streamlit e a API FastAPI utilizam o mesmo serviço central, evitando duplicação da lógica.

Mais detalhes em [ARCHITECTURE.md](ARCHITECTURE.md).

## Perfis de execução

| Perfil | Motor principal | Reranker | Parser avançado | Indicado para |
|---|---|---:|---:|---|
| `demo` | MiniLM/ONNX ou fallback local | Não | Não | apresentação e notebooks com CPU |
| `balanced` | E5-small/ONNX ou fallback local | Top 3 | Não | equilíbrio entre qualidade e velocidade |
| `complete` | BGE-M3 | BGE Reranker | Docling + Presidio | máquinas mais fortes |

O modo de fallback com TF-IDF e RapidFuzz permanece disponível mesmo sem os modelos opcionais.

## Início rápido

### Requisitos

- Windows, Linux ou macOS;
- Python `3.11`, `3.12` ou `3.13`;
- Git;
- VS Code recomendado.

### 1. Clone o repositório

```powershell
git clone https://github.com/viniciusrodriguesai/resume-agent-system.git
cd resume-agent-system
```

### 2. Crie e ative o ambiente virtual

#### Windows PowerShell

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

#### Linux ou macOS

```bash
python3.11 -m venv .venv
source .venv/bin/activate
```

### 3. Instale as dependências

#### Versão base

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

#### Versão com IA local recomendada

```powershell
python -m pip install -r requirements-ai.txt
python scripts\preload_models.py --profile demo
```

#### Versão completa

```powershell
python -m pip install -r requirements-full.txt
python scripts\preload_models.py --profile complete
```

### 4. Execute a interface

```powershell
python -m streamlit run app.py
```

Abra no navegador:

```text
http://localhost:8501
```

No Windows, também é possível usar os scripts `.bat` incluídos no repositório.

## Uso

1. Escolha um perfil de execução.
2. Cole ou envie o currículo.
3. Cole ou envie a descrição da vaga.
4. Selecione o rigor da análise.
5. Execute o fluxo multiagente.
6. Analise a pontuação, as evidências e as recomendações.
7. Exporte o relatório.

### O resultado inclui

- compatibilidade geral;
- notas por categoria;
- requisitos encontrados, parciais e ausentes;
- melhor evidência para cada requisito;
- motor utilizado na comparação;
- relatório de privacidade;
- histórico dos agentes;
- recomendações priorizadas;
- arquivos para download.

## API local

Inicie a API:

```powershell
python -m uvicorn api.main:app --reload
```

Documentação interativa:

```text
http://127.0.0.1:8000/docs
```

### Endpoints principais

| Método | Endpoint | Descrição |
|---|---|---|
| `GET` | `/health` | verifica a saúde da aplicação |
| `POST` | `/v1/analyze` | executa uma análise |
| `GET` | `/v1/profiles` | lista os perfis disponíveis |
| `GET` | `/metrics` | expõe métricas quando habilitadas |

Uma chave pode ser configurada por meio da variável:

```text
RESUME_API_KEY
```

## Arquitetura

```text
resume-agent-system/
├── api/                    # API FastAPI
├── assets/                 # estilos e recursos do frontend
├── data/                   # bancos locais ignorados pelo Git
├── docs/                   # documentação complementar
├── examples/               # currículo e vaga de demonstração
├── resume_ai/              # domínio, serviços e agentes
├── scripts/                # instalação, modelos e manutenção
├── tests/                  # testes automatizados
├── app.py                  # interface Streamlit
├── pyproject.toml          # metadados e configuração
├── requirements*.txt       # conjuntos de dependências
├── Dockerfile
└── docker-compose.yml
```

### Separação de responsabilidades

```text
Streamlit ─┐
           ├──► serviço de análise ───► agentes ───► evidências
FastAPI ───┘                                  │
                                              ▼
                                  pontuação, revisão e relatórios
```

O núcleo não depende do Streamlit nem do FastAPI, permitindo trocar a interface sem reescrever o pipeline.

## Privacidade e segurança

As principais proteções são:

- anonimização antes de busca semântica e cache;
- ausência de currículos e vagas nos logs;
- histórico mínimo em SQLite;
- validação de PDF e DOCX;
- limite de upload;
- proteção opcional da API;
- segredos e bancos locais ignorados pelo Git;
- auditoria automática das dependências no CI.

Leia [SECURITY.md](SECURITY.md) antes de expor a aplicação em rede.

> [!WARNING]
> Não exponha o Streamlit diretamente na internet sem autenticação, HTTPS, limitação de acesso e revisão adicional de segurança.

## Configuração

As configurações podem ser definidas por variáveis de ambiente.

Exemplo para uma execução leve:

```powershell
$env:RESUME_AI_ENABLE_EMBEDDINGS="1"
$env:RESUME_AI_ENABLE_RERANKER="0"
$env:RESUME_AI_ENABLE_DOCLING="0"
$env:RESUME_AI_TOP_K="3"
```

Consulte `.env.example` e os arquivos de configuração do projeto para todas as opções disponíveis.

## Desenvolvimento

Instale as dependências de desenvolvimento:

```powershell
python -m pip install -r requirements-dev.txt
```

Execute as verificações:

```powershell
python -m ruff check .
python -m mypy resume_ai
python -m pytest
python -m pip_audit -r requirements.txt
```

### Cobertura

```powershell
python -m pytest --cov=resume_ai --cov-report=term-missing
```

### Interface

```powershell
python -m streamlit run app.py
```

### API

```powershell
python -m uvicorn api.main:app --reload
```

## Docker

### Construção e execução

```powershell
docker compose up --build
```

Depois, acesse:

```text
Streamlit: http://localhost:8501
FastAPI:   http://localhost:8000/docs
```

Os modelos grandes não são incluídos diretamente na imagem para evitar builds excessivamente pesados.

## Qualidade e CI

A integração contínua executa:

- Ruff;
- pytest com cobertura;
- pip-audit.

O workflow é iniciado em pushes e pull requests.

## Limitações

- a extração pode falhar em documentos com layouts muito complexos;
- modelos locais podem ser lentos em CPU;
- o catálogo de competências pode não cobrir todos os domínios;
- similaridade textual não comprova experiência real;
- as pontuações precisam ser calibradas com dados de avaliação;
- o sistema pode reproduzir vieses presentes nos textos e modelos;
- o resultado não substitui entrevistas, testes técnicos ou avaliação humana.

## Uso responsável

Este projeto foi desenvolvido para:

- apoiar candidatos na adaptação de seus currículos;
- demonstrar sistemas multiagentes e IA explicável;
- estudar correspondência semântica entre documentos;
- apoiar análises humanas com evidências.

Não deve ser usado como único critério para:

- rejeitar candidatos;
- decidir contratações;
- inferir características pessoais;
- criar rankings definitivos de pessoas.

## Roadmap

- [x] análise local com fallback offline;
- [x] frontend Streamlit;
- [x] API FastAPI;
- [x] anonimização antes dos embeddings;
- [x] evidências por requisito;
- [x] relatórios exportáveis;
- [x] testes e CI;
- [ ] dataset público de avaliação;
- [ ] calibração automática dos limiares;
- [ ] avaliação de viés por grupo e cenário;
- [ ] suporte aprimorado a currículos em duas colunas;
- [ ] benchmark entre motores semânticos;
- [ ] internacionalização completa da interface;
- [ ] documentação de contribuição mais detalhada.

## Contribuição

Contribuições são bem-vindas.

1. Crie um fork.
2. Crie uma branch:

```bash
git checkout -b feature/minha-melhoria
```

3. Faça as alterações e execute os testes.
4. Envie commits objetivos.
5. Abra um Pull Request explicando o problema e a solução.

Antes de contribuir, consulte a documentação do projeto e mantenha dados pessoais fora de testes, issues e exemplos.

## Suporte

Para relatar erros ou sugerir melhorias, abra uma issue:

```text
https://github.com/viniciusrodriguesai/resume-agent-system/issues
```

Inclua:

- sistema operacional;
- versão do Python;
- perfil utilizado;
- mensagem de erro;
- passos para reproduzir;
- logs sem dados pessoais.

## Licença

Distribuído sob a licença MIT. Consulte [LICENSE](LICENSE).

## Autor

Desenvolvido por **Vinicius Mangueira**.

GitHub: [@viniciusrodriguesai](https://github.com/viniciusrodriguesai)

---

<div align="center">

**Local-first · Explainable · Multi-agent · Privacy-aware**

</div>
