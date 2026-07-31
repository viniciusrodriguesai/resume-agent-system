<div align="center">

# Resume Match AI

### Análise local, explicável e multiagente de currículos e vagas

Compare requisitos, encontre evidências no currículo, identifique lacunas e gere recomendações sem depender de APIs pagas e sem enviar os documentos para serviços externos.

[![Version](https://img.shields.io/badge/version-5.2.1-5B5BD6)](https://github.com/viniciusrodriguesai/resume-agent-system)
[![Python](https://img.shields.io/badge/Python-3.11%20%E2%80%93%203.13-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![CI](https://github.com/viniciusrodriguesai/resume-agent-system/actions/workflows/ci.yml/badge.svg)](https://github.com/viniciusrodriguesai/resume-agent-system/actions/workflows/ci.yml)
[![Streamlit](https://img.shields.io/badge/UI-Streamlit-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io/)
[![FastAPI](https://img.shields.io/badge/API-FastAPI-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/license-MIT-yellow.svg)](LICENSE)
[![Local First](https://img.shields.io/badge/AI-local--first-111827)](#privacidade-e-segurança)
[![Academic Project](https://img.shields.io/badge/projeto-acad%C3%AAmico-Programa%C3%A7%C3%A3o%20com%20Agentes-7C3AED)](#contexto-acad%C3%AAmico)

[Visão geral](#visão-geral) ·
[Recursos](#principais-recursos) ·
[Instalação](#início-rápido) ·
[Arquitetura](#arquitetura) ·
[API](#api-local) ·
[Segurança](#privacidade-e-segurança)

</div>

---

## Visão geral

O **Resume Match AI** é uma aplicação open source que compara um currículo com uma descrição de vaga e produz uma análise estruturada, explicável e auditável.

Em vez de retornar apenas uma porcentagem, o sistema mostra:

- quais requisitos foram atendidos;
- quais foram parcialmente atendidos;
- quais não possuem evidência suficiente;
- o trecho do currículo usado como evidência;
- como a nota foi formada;
- recomendações priorizadas para melhorar o currículo;
- o tempo de execução de cada agente;
- um relatório de privacidade;
- relatórios para download em Markdown, JSON e CSV.

A versão atual é a **5.2.1** e foi projetada para funcionar localmente em computadores com CPU, mantendo opções mais pesadas para máquinas com maior capacidade.

> [!IMPORTANT]
> O sistema oferece apoio à análise humana. Ele não deve ser usado como único critério para selecionar, rejeitar ou classificar pessoas.


## Contexto acadêmico

Este projeto foi desenvolvido para a disciplina **Programação com Agentes**, ministrada pelo professor **Andrei de Araujo Formiga**.

A proposta da disciplina é aprender a programar melhor com o apoio de agentes de inteligência artificial, usando a IA não apenas para gerar trechos isolados de código, mas como parte ativa de todo o processo de desenvolvimento de software.

No projeto, os agentes de IA foram utilizados para apoiar atividades como:

- levantamento e refinamento de requisitos;
- definição da arquitetura;
- implementação de funcionalidades;
- revisão e refatoração de código;
- criação de testes;
- identificação de erros;
- melhoria da documentação;
- análise de segurança;
- organização do projeto para apresentação e evolução futura.

O objetivo acadêmico não é substituir o aprendizado de programação, mas desenvolver a capacidade de:

- formular instruções técnicas claras;
- avaliar criticamente código produzido por IA;
- validar resultados;
- detectar erros e inconsistências;
- compreender decisões de arquitetura;
- melhorar código de forma iterativa;
- usar agentes como ferramentas de engenharia de software.

Este repositório representa, portanto, tanto o resultado funcional do sistema quanto o processo de aprendizagem sobre desenvolvimento assistido por agentes.

### Informações da disciplina

| Item | Informação |
|---|---|
| Disciplina | Programação com Agentes |
| Professor | Andrei de Araujo Formiga |
| Tipo de trabalho | Projeto final |
| Tema | Sistema multiagente para análise de currículos e vagas |
| Objetivo acadêmico | Aprender a programar e desenvolver software de forma mais eficiente com agentes de IA |

## Problema

Comparadores tradicionais dependem de palavras exatas e podem falhar quando currículo e vaga descrevem a mesma competência de maneiras diferentes.

Exemplo:

```text
Vaga: experiência com modelagem preditiva
Currículo: desenvolvimento de modelos de machine learning
```

O Resume Match AI combina técnicas lexicais, aproximação textual e similaridade semântica para encontrar relações como essa, mantendo a evidência utilizada visível ao usuário.

## Principais recursos

### Análise multiagente

O fluxo é dividido em agentes especializados:

1. **Agente de privacidade** — remove identificadores pessoais antes da análise.
2. **Agente de currículo** — estrutura competências, formação, experiência e projetos.
3. **Agente de vaga** — extrai requisitos e classifica prioridades.
4. **Agente de evidências** — encontra os melhores trechos do currículo para cada requisito.
5. **Agente de pontuação** — calcula notas por requisito e categoria.
6. **Agente revisor** — verifica inconsistências e casos limítrofes.
7. **Agente de recomendações** — sugere melhorias sem inventar experiências.
8. **Agente de relatórios** — gera saídas legíveis e exportáveis.

### Correspondência explicável

- evidência específica para cada requisito;
- status **Correspondido**, **Parcial** ou **Ausente**;
- prioridade **Obrigatória**, **Desejável** ou **Neutra**;
- detalhamento das notas lexical, aproximada, semântica e final;
- explicação textual da pontuação;
- notas por categoria;
- identificação de requisitos obrigatórios ausentes.

### Execução local

- nenhum serviço pago obrigatório;
- fallback offline com TF-IDF e RapidFuzz;
- embeddings locais opcionais;
- modelos ONNX para execução eficiente em CPU;
- reranker opcional;
- cache de embeddings e resultados;
- histórico local mínimo em SQLite.

### Documentos

- texto colado diretamente na interface;
- upload de PDF, DOCX e TXT;
- limite padrão de 10 MB;
- validação de extensão e estrutura do arquivo;
- parsing leve com `pypdf` e `python-docx`;
- Docling opcional para documentos mais complexos.

### Interface e API

- dashboard em Streamlit;
- gráficos com Plotly;
- exemplo de currículo e vaga carregado com um clique;
- API local com FastAPI;
- documentação OpenAPI automática;
- Dockerfile para execução isolada.

### Qualidade de software

- modelos de domínio tipados com Pydantic;
- lint com Ruff;
- checagem estática com mypy;
- testes com pytest;
- cobertura de testes;
- auditoria de dependências com pip-audit;
- integração contínua com GitHub Actions;
- atualizações automatizadas com Dependabot.

## O que mudou na V5.2

### Hotfix V5.2.1

- limpa automaticamente resultados de sessão incompatíveis após uma atualização;
- impede falha de validação do Pydantic ao abrir resultados antigos;
- orienta o usuário a executar uma nova análise quando necessário.


- classificação mais clara em baixa, moderada, boa, alta e excelente compatibilidade;
- correção do texto de nível exibido no cartão principal;
- cards renomeados para Correspondidos e Parcialmente atendidos;
- separação visual entre requisitos desejáveis e obrigatórios ausentes;
- aviso positivo quando todos os requisitos obrigatórios possuem evidência;
- resumo automático da compatibilidade;
- destaque dos principais pontos fortes e das principais lacunas;
- cartão principal mais compacto;
- relatórios atualizados com os novos indicadores;
- cache de análises versionado para impedir reutilização de resultados antigos.

## Como funciona

```text
Currículo + vaga
      │
      ▼
Agente de privacidade
      │
      ▼
Estruturação do currículo e da vaga
      │
      ▼
Extração e priorização de requisitos
      │
      ▼
Motor de evidências
      ├── TF-IDF
      ├── RapidFuzz
      ├── embeddings locais
      └── reranker opcional
      │
      ▼
Pontuação explicável
      │
      ▼
Agente revisor
      │
      ├── revisão necessária ──► nova passagem
      └── aprovado
      │
      ▼
Recomendações + relatórios
```

## Perfis de execução

| Perfil | Modelo principal | Backend | Reranker | Parser avançado | Indicado para |
|---|---|---|---:|---:|---|
| `demo` | `paraphrase-multilingual-MiniLM-L12-v2` | ONNX | Não | Não | apresentação e CPU |
| `balanced` | `multilingual-e5-small` | ONNX | Top 3 | Não | equilíbrio entre qualidade e velocidade |
| `complete` | `BAAI/bge-m3` | PyTorch | BGE Reranker | Docling + Presidio | máquinas mais fortes |

O modo de fallback continua disponível quando os modelos opcionais não podem ser carregados.

## Tecnologias

| Camada | Tecnologias |
|---|---|
| Linguagem | Python 3.11–3.13 |
| Interface | Streamlit |
| API | FastAPI + Uvicorn |
| Modelagem | Pydantic + pydantic-settings |
| Busca lexical | scikit-learn + TF-IDF |
| Similaridade aproximada | RapidFuzz |
| IA local | Sentence Transformers + ONNX Runtime |
| Modelos opcionais | MiniLM, E5-small, BGE-M3 e BGE Reranker |
| Documentos | pypdf, python-docx e Docling opcional |
| Privacidade | regras locais e Presidio opcional |
| Dados | SQLite e LanceDB opcional |
| Gráficos | Plotly |
| Testes | pytest |
| Qualidade | Ruff, mypy e pip-audit |
| Empacotamento | Docker |

## Início rápido

### Requisitos

- Windows, Linux ou macOS;
- Python 3.11, 3.12 ou 3.13;
- Git;
- VS Code recomendado;
- conexão com a internet apenas para a instalação inicial e o download dos modelos opcionais.

### 1. Clone o repositório

```powershell
git clone https://github.com/viniciusrodriguesai/resume-agent-system.git
cd resume-agent-system
```

### 2. Crie o ambiente virtual

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

### 3. Atualize o instalador

```powershell
python -m pip install --upgrade pip
```

### 4. Escolha a instalação

#### Base

Instala a interface, a API e o fallback totalmente local:

```powershell
python -m pip install -r requirements.txt
```

#### IA local recomendada

Instala embeddings locais e o backend ONNX:

```powershell
python -m pip install -r requirements-ai.txt
python scripts\preload_models.py --profile demo
```

#### Completa

Instala os componentes opcionais mais pesados:

```powershell
python -m pip install -r requirements-full.txt
python scripts\preload_models.py --profile complete
```

> [!NOTE]
> O perfil completo pode usar vários gigabytes de armazenamento e ser lento em computadores sem GPU.

## Executar a interface

```powershell
python -m streamlit run app.py
```

A aplicação ficará disponível em:

```text
http://localhost:8501
```

O Streamlit normalmente abre o navegador automaticamente. Caso isso não aconteça:

```powershell
Start-Process "http://localhost:8501"
```

Para solicitar a abertura automática:

```powershell
python -m streamlit run app.py --server.headless false
```

Para encerrar:

```text
Ctrl + C
```

## Uso da interface

1. Escolha o perfil de execução.
2. Selecione o rigor da análise.
3. Escolha entre colar textos ou enviar arquivos.
4. Insira o currículo e a vaga.
5. Clique em **Executar análise multiagente**.
6. Consulte as abas:
   - Visão geral;
   - Evidências;
   - Recomendações;
   - Privacidade;
   - Agentes;
   - Exportar.
7. Baixe o relatório no formato desejado.

Para uma apresentação em notebook com CPU, use:

```text
Perfil: Demonstração
Rigor: Equilibrado
Entrada: Colar textos
```

## API local

Inicie a API:

```powershell
python -m uvicorn api.main:app --reload
```

A documentação interativa será aberta em:

```text
http://127.0.0.1:8000/docs
```

A especificação OpenAPI estará disponível em:

```text
http://127.0.0.1:8000/openapi.json
```

Endpoints disponíveis no projeto:

| Método | Endpoint | Função |
|---|---|---|
| `GET` | `/health` | verifica a saúde da API |
| `GET` | `/v1/profiles` | lista os perfis de execução |
| `POST` | `/v1/analyze` | executa uma análise |
| `GET` | `/metrics` | expõe métricas quando habilitadas |

A API pode ser protegida com:

```powershell
$env:RESUME_API_KEY="uma-chave-segura"
```

## Configuração

As opções podem ser definidas por variáveis de ambiente com o prefixo `RESUME_` ou em um arquivo `.env`.

Exemplo de execução leve:

```powershell
$env:RESUME_PROFILE="demo"
$env:RESUME_EMBEDDING_ENABLED="true"
$env:RESUME_EMBEDDING_BACKEND="onnx"
$env:RESUME_EMBEDDING_DEVICE="cpu"
$env:RESUME_RERANKER_ENABLED="false"
$env:RESUME_DOCLING_ENABLED="false"
$env:RESUME_PRESIDIO_ENABLED="false"
$env:RESUME_TOP_K="3"
```

Outras configurações relevantes:

| Variável | Padrão | Descrição |
|---|---:|---|
| `RESUME_MAX_UPLOAD_MB` | `10` | tamanho máximo do arquivo |
| `RESUME_MAX_DOCUMENT_CHARS` | `30000` | limite de caracteres processados |
| `RESUME_MAX_REQUIREMENTS` | `30` | quantidade máxima de requisitos |
| `RESUME_CACHE_ENABLED` | `true` | ativa o cache local |
| `RESUME_HISTORY_ENABLED` | `true` | ativa o histórico mínimo |
| `RESUME_STORE_RAW_DOCUMENTS` | `false` | impede armazenamento do documento bruto |
| `RESUME_STORE_ANONYMIZED_DOCUMENTS` | `false` | impede armazenamento do texto anonimizado |
| `RESUME_LOG_PII` | `false` | impede dados pessoais nos logs |
| `RESUME_REQUIRE_LOGIN` | `false` | ativa autenticação quando configurada |
| `RESUME_VECTOR_STORE` | `memory` | usa memória ou LanceDB |

## Arquitetura

```text
Streamlit ─┐
           ├──► ResumeAnalysisService
FastAPI ───┘             │
                         ├──► domínio tipado
                         ├──► agentes
                         ├──► motor de evidências
                         ├──► pontuação e revisão
                         ├──► recomendações
                         └──► relatórios
                                  │
                                  ├── cache local
                                  └── histórico mínimo
```

A lógica principal não depende diretamente do Streamlit nem do FastAPI. Isso permite trocar a interface sem reescrever o pipeline.

### Estrutura do projeto

```text
resume-agent-system/
├── api/                     # API FastAPI
├── assets/                  # estilos da interface
├── data/                    # histórico local ignorado pelo Git
├── docs/                    # documentação complementar
├── examples/                # currículo e vaga de demonstração
├── resume_ai/
│   ├── application/         # casos de uso
│   ├── domain/              # modelos e regras
│   ├── infrastructure/      # documentos, persistência e IA
│   └── presentation/        # componentes de apresentação
├── scripts/                 # instalação e download de modelos
├── tests/                   # testes automatizados
├── app.py                   # aplicação Streamlit
├── pyproject.toml           # metadados e ferramentas
├── requirements.txt         # dependências base
├── requirements-ai.txt      # IA local
├── requirements-full.txt    # componentes completos
├── requirements-dev.txt     # desenvolvimento
├── Dockerfile
├── ARCHITECTURE.md
├── SECURITY.md
└── README.md
```

Mais detalhes em [ARCHITECTURE.md](ARCHITECTURE.md).

## Privacidade e segurança

O projeto aplica privacidade antes da análise semântica:

- identificadores pessoais são removidos antes dos embeddings;
- currículo e vaga não são registrados nos logs;
- o histórico guarda apenas metadados, pontuação e tempos;
- documentos brutos não são armazenados por padrão;
- arquivos aceitos são limitados a PDF, DOCX e TXT;
- uploads possuem limite de tamanho;
- PDF e DOCX passam por validação básica;
- segredos, bancos, caches e arquivos `.env` são ignorados pelo Git;
- a API possui chave opcional;
- o CI executa auditoria de dependências.

> [!WARNING]
> Não exponha a interface diretamente na internet sem autenticação, HTTPS, controle de acesso e revisão adicional de segurança.

Leia [SECURITY.md](SECURITY.md) antes de disponibilizar a aplicação em rede.

## Testes e qualidade

Instale as dependências de desenvolvimento:

```powershell
python -m pip install -r requirements-dev.txt
```

Execute a suíte:

```powershell
python -m pytest
```

Verifique o código:

```powershell
python -m ruff check .
python -m mypy resume_ai
```

Gere cobertura:

```powershell
python -m pytest --cov=resume_ai --cov-report=term-missing
```

Audite dependências:

```powershell
python -m pip_audit -r requirements.txt
```

## Integração contínua

O workflow de CI é executado em pushes e pull requests e inclui:

- instalação em Python 3.11;
- Ruff;
- pytest com cobertura;
- pip-audit.

O status atual aparece no badge no início deste README.

## Docker

Construa a imagem:

```powershell
docker build -t resume-match-ai:5.2 .
```

Execute:

```powershell
docker run --rm -p 8501:8501 resume-match-ai:5.2
```

Abra:

```text
http://localhost:8501
```

A imagem usa Python 3.11 slim, executa com usuário sem privilégios e possui health check do Streamlit.

## Desempenho

O tempo de análise depende de:

- perfil escolhido;
- tamanho dos documentos;
- quantidade de requisitos;
- disponibilidade de CPU ou GPU;
- modelo utilizado;
- uso de reranker e parser avançado;
- estado do cache.

Recomendações para CPU:

```text
Perfil: demo
Backend: ONNX
Batch: 32
Top-k: 3
Reranker: desativado
Docling: desativado
```

A primeira execução pode ser mais lenta porque o modelo precisa ser carregado. As seguintes tendem a usar o cache.

## Limitações

- a extração pode falhar em PDFs com layouts muito complexos;
- similaridade textual não comprova experiência real;
- modelos locais podem ser lentos em CPU;
- o catálogo de competências pode não cobrir todos os domínios;
- a pontuação precisa ser calibrada com dados representativos;
- modelos e textos podem reproduzir vieses;
- o sistema não substitui entrevistas, testes técnicos ou revisão humana;
- a qualidade da análise depende da clareza do currículo e da vaga.

## Uso responsável

O projeto foi criado para:

- ajudar candidatos a revisar currículos;
- demonstrar sistemas multiagentes;
- estudar busca semântica e IA explicável;
- apoiar análises humanas com evidências;
- gerar relatórios locais de compatibilidade.

Não deve ser usado como único critério para:

- rejeitar candidatos;
- decidir contratações;
- inferir atributos sensíveis;
- gerar rankings definitivos de pessoas;
- automatizar decisões de alto impacto sem supervisão.

## Roadmap

- [x] fallback offline;
- [x] embeddings locais;
- [x] perfis de execução;
- [x] anonimização antes dos embeddings;
- [x] evidências por requisito;
- [x] interface Streamlit;
- [x] API FastAPI;
- [x] relatórios exportáveis;
- [x] histórico mínimo;
- [x] testes e CI;
- [x] Docker;
- [ ] benchmark público entre modelos;
- [ ] dataset de avaliação anonimizado;
- [ ] calibração automática dos limiares;
- [ ] avaliação sistemática de viés;
- [ ] suporte aprimorado a currículos em duas colunas;
- [ ] internacionalização completa;
- [ ] SBOM e verificação de procedência;
- [ ] isolamento reforçado do parser;
- [ ] registro de modelos confiáveis por hash.

## Contribuição

Contribuições são bem-vindas.

1. Faça um fork.
2. Crie uma branch:

```bash
git checkout -b feature/minha-melhoria
```

3. Implemente a alteração.
4. Execute testes, lint e auditoria.
5. Faça commits objetivos.
6. Abra um Pull Request descrevendo:
   - problema;
   - solução;
   - testes executados;
   - impactos de segurança e privacidade.

Nunca envie currículos reais, dados pessoais, tokens ou segredos em commits, testes, issues ou pull requests.

## Suporte

Para relatar um erro ou sugerir uma melhoria, abra uma issue no repositório.

Inclua:

- sistema operacional;
- versão do Python;
- perfil utilizado;
- etapas para reproduzir;
- mensagem de erro;
- logs sem dados pessoais.

## Licença

Distribuído sob a licença MIT. Consulte [LICENSE](LICENSE).

## Autor e orientação acadêmica

Desenvolvido por **Vinicius Mangueira** como projeto da disciplina **Programação com Agentes**.

Professor da disciplina: **Andrei de Araujo Formiga**.

GitHub: [@viniciusrodriguesai](https://github.com/viniciusrodriguesai)

---

<div align="center">

**Local-first · Explainable · Multi-agent · Privacy-aware**

</div>
