# Resume Match AI 6.0.1

Patch de estabilização da versão 6.0.0, produzido após auditoria adversarial dos
contratos de matching, scoring, privacidade, uploads, API, cache, SQLite,
concorrência, Streamlit, observabilidade e empacotamento.

## Correções

- reconhece negações inglesas qualificadas, como `no professional experience with
  Java`, sem promovê-las a evidência positiva;
- diferencia leitura superficial sobre uma tecnologia de experiência operacional;
- preserva linhas técnicas reconhecidas logo abaixo de cabeçalhos de currículo
  quando o documento não contém uma linha de nome;
- torna concorrentes as publicações do cache JSON sem colisão de arquivos
  temporários no Windows;
- aplica `cache_max_entries` também ao backend JSON, com remoção das entradas mais
  antigas;
- rejeita `Content-Length` negativo como cabeçalho inválido antes do processamento
  do corpo;
- contém falhas do backend na interface Streamlit sem expor detalhes privados nem
  manter resultado anterior enganoso;
- preserva conceitos literais separados por vírgula ou ponto-e-vírgula em requisitos
  cumulativos e impede cobertura incompleta de virar correspondência completa;
- aplica o envelope de erro seguro e correlacionado também a respostas de roteamento
  `404` e `405`.

## Regressões adicionadas

- requisitos cumulativos e alternativos em português e inglês, inclusive três
  competências coordenadas;
- negações sintéticas de Docker, AWS, Kubernetes e Java;
- contraste entre menção superficial e operação de Kubernetes em produção;
- invariantes de score para zero requisitos, todos ausentes, todos atendidos e
  repetição proporcional;
- nomes rotulados e Unicode em português, coreano e chinês, preservando texto
  técnico subsequente;
- isolamento entre dois currículos com sentinels exclusivos;
- concorrência e eviction do cache JSON;
- autenticação de produção, rate limit, JSON inválido, Content-Type incompatível,
  request IDs, CORS, métricas e erros HTTP controlados;
- falha sintética do backend no Streamlit sem vazamento de e-mail ou caminho local.

## Validação

- Python 3.11: 244 testes aprovados;
- cobertura de `resume_ai`: 88%;
- Ruff: aprovado;
- mypy: aprovado em 60 arquivos fonte;
- `pip-audit` runtime e desenvolvimento: nenhuma vulnerabilidade conhecida;
- wheel e sdist: construídos e inspecionados, com datasets necessários e sem testes,
  bancos, caches, segredos ou arquivos temporários;
- smoke do wheel em ambiente limpo: imports, metadados de distribuição e versão
  `6.0.1` aprovados, com `pip check` sem dependências quebradas;
- API instalada pelo wheel: `/health`, `/ready` e `/v1/profiles` responderam com
  sucesso sem carregar modelos pesados;
- Streamlit instalado pelo wheel: inicialização headless e endpoint de saúde
  aprovados;
- `pip check`: aprovado;
- Docker Compose: configuração válida;
- runtime Docker: não validado porque o daemon não estava disponível;
- Python 3.13 local: não validado porque o launcher aponta para uma instalação
  ausente.
