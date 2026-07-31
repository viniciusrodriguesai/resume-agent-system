# Analisador Multiagente de Currículos e Vagas — V4

Sistema local, multilíngue e explicável para comparar currículos com descrições de vagas.
A interface, os relatórios e a documentação estão em português.

## O que mudou na V4

- Orquestração por grafo com LangGraph e rota condicional de revisão.
- Recuperação semântica multilíngue com BGE-M3.
- Reranqueamento de evidências com BGE Reranker v2 M3.
- Leitura estruturada de PDF e DOCX com Docling.
- Anonimização de dados pessoais com Microsoft Presidio.
- Catálogo local de competências preparado para importar o ESCO.
- Combinação de embeddings, TF-IDF e RapidFuzz.
- Evidência textual para cada requisito da vaga.
- Pontuação por categoria, prioridade e criticidade.
- Agente revisor que pode solicitar uma segunda passagem.
- Histórico local em SQLite.
- Exportação em Markdown, JSON e CSV.
- Avaliação experimental com precisão, recall, F1 e matriz de confusão.
- Testes da lógica e da interface Streamlit.
- GitHub Actions para testar cada push.

## Agentes

1. **Agente de Privacidade e Justiça** — remove dados pessoais antes da comparação.
2. **Agente de Currículo** — estrutura competências, formação, experiência e projetos.
3. **Agente de Vaga** — identifica requisitos obrigatórios, desejáveis e responsabilidades.
4. **Agente de Recuperação e Reranqueamento** — encontra as melhores evidências no currículo.
5. **Agente de Pontuação Explicável** — calcula a compatibilidade geral e por categoria.
6. **Agente Revisor e Auditor** — verifica inconsistências e pode solicitar nova busca.
7. **Agente de Recomendações** — gera ações priorizadas sem inventar experiências.
8. **Agente de Relatório** — produz os arquivos finais.

## Instalação recomendada no VS Code

### Modo base

Funciona sem baixar modelos grandes. Utiliza TF-IDF e RapidFuzz.

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

### Modo de IA completa

Instala Docling, Presidio, BGE-M3 e o reranker multilíngue.

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-full.txt
python scriptsaixar_modelos.py
python -m streamlit run app.py
```

A primeira execução pode demorar porque os modelos são baixados. Depois eles ficam no cache local.

## Atalhos no Windows

- `instalar_base.bat` — instala o modo base e inicia.
- `instalar_ia_completa.bat` — instala a IA completa, baixa os modelos e inicia.
- `executar.bat` — inicia uma instalação já pronta.
- `testar.bat` — executa os testes.

## Testar

```powershell
python -m pytest -q
```

## Executar a demonstração

```powershell
python run_demo.py
```

## Importar o ESCO

Baixe um pacote CSV oficial do ESCO e execute:

```powershell
python scripts\importar_esco.py caminho\para\skills_pt.csv
```

A aplicação passará a utilizar o catálogo importado no lugar da amostra local.

## Avaliar cientificamente

```powershell
python scriptsvaliar_dataset.py data\dataset_avaliacao_exemplo.csv
```

O script calcula relatório de classificação e matriz de confusão.

## Estrutura

```text
resume-agent-system-v4-portugues/
├── app.py
├── resume_v4/
│   ├── agentes/
│   ├── services/
│   ├── utils/
│   └── workflow.py
├── data/
├── docs/
├── examples/
├── scripts/
├── tests/
├── requirements.txt
└── requirements-full.txt
```

## Limitação ética

O sistema é uma ferramenta de apoio. Não deve tomar decisões automáticas de contratação nem utilizar nome, contato, localização, idade, deficiência ou outros atributos pessoais para pontuar candidatos.
