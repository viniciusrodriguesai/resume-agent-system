# Resume Match AI 6.0.0

Release de engenharia que consolida o runtime local existente, preserva o pipeline
de oito agentes e endurece seus limites de segurança, privacidade, operação e
distribuição.

## Added

- contrato de erro tipado e seguro para a API, com `request_id` em todas as falhas;
- endpoint `/ready`, correlação de requisições e exposição CORS de
  `X-Request-ID`;
- telemetria JSON estruturada por agente e por pipeline, com métricas locais de
  latência, cache, warnings, fallback e requisitos;
- framework reprodutível de avaliação para retrieval e pipeline completo, com
  datasets sintéticos versionados e registro do backend realmente carregado;
- porta injetável de histórico e implementação SQLite explicitamente nomeada;
- controles de retenção, limite de consulta e `busy_timeout` do histórico;
- build PEP 517 de wheel e sdist, incluindo os datasets de avaliação necessários.

## Changed

- o histórico SQLite persiste somente resumo operacional: ID, data, perfil, score,
  nível, timings e estado de backend permitido;
- o cache local usa somente memória ou JSON com opt-in explícito para documentos
  anonimizados; o backend inseguro baseado em pickle foi removido;
- os extras de IA usam a pilha Torch compatível com
  `sentence-transformers>=5.7,<6` e `transformers>=5.5,<6`;
- o pacote deixou de declarar dependências diretas sem uso em runtime, incluindo
  LanceDB, scikit-learn, python-multipart, LangGraph, structlog e extras inativos de
  OpenTelemetry;
- o Compose publica Streamlit e API apenas em loopback e usa `/ready` no healthcheck
  da API;
- o Dockerfile copia somente arquivos necessários ao runtime e fixa a imagem base
  por digest.

## Fixed

- requisitos cumulativos agora exigem todos os conceitos para `matched`, preservam
  evidência comprovada de subconjunto como `partial` e mantêm alternativas com
  `ou`/`or`;
- nomes rotulados ou logo abaixo de cabeçalhos de currículo são anonimizados sem
  remover linhas técnicas subsequentes;
- preflight CORS aceita `X-Request-ID` e respostas inesperadas preservam correlação;
- `/ready` e o status da API informam o backend de embeddings realmente configurado;
- TXT com BOM, PDFs truncados ou com cauda e erros controlados de parser recebem
  tratamento determinístico.

## Security

- validação de MIME, extensão, nome de arquivo, PDF, DOCX/OOXML e caracteres de
  controle antes do parsing;
- extração de PDF e DOCX limitada durante a leitura para reduzir exaustão de
  recursos;
- limite do corpo de `/v1/analyze` aplicado durante streaming, antes da
  desserialização, inclusive para `Content-Length` enganoso;
- erros de validação, HTTP, parser, modelo e falhas inesperadas não ecoam payload,
  stack trace, caminho local ou mensagem privada;
- logs, diagnósticos de agente e estado persistido usam allowlists e sanitização
  contra PII;
- SQLite usa WAL, `secure_delete`, timeout de concorrência, versão de schema,
  migração e retenção determinística;
- Actions de terceiros foram fixadas por SHA e as dependências vulneráveis da pilha
  de modelos foram restringidas a versões corrigidas.

## Performance

- embeddings de trechos são calculados em lote e reutilizados por uma cache local
  limitada;
- retrieval agrupa candidatos e mantém fallback lexical com TF-IDF e RapidFuzz;
- parsing de PDF e DOCX encerra ao atingir o limite configurado, sem extrair o
  documento inteiro primeiro.

## Testing

- CI separa e executa testes unitários, de integração, segurança e avaliação;
- regressões cobrem uploads hostis, limites da API, erros sanitizados, correlação,
  telemetria, persistência, matching cumulativo, negação e invariantes de scoring;
- CI valida Ruff, mypy, auditoria de dependências, wheel e sdist;
- o sdist exclui a árvore de testes e os artefatos privados permanecem fora das
  distribuições.

## Documentation

- arquitetura, API, autenticação, configuração, deployment, observabilidade,
  segurança e avaliação foram alinhados ao runtime V6;
- guias operacionais V5 superados foram removidos; referências históricas foram
  preservadas quando continuam corretas.

## Breaking Changes

- clientes da API devem consumir o envelope de erro
  `{"error":{"code":"...","message":"...","request_id":"..."}}` em vez do
  campo `detail` padrão do FastAPI;
- o Compose deixa de expor portas em todas as interfaces por padrão; acesso remoto
  requer configuração explícita do operador;
- a migração SQLite remove títulos de vaga previamente persistidos, por
  minimização de dados;
- importações diretas da classe interna `HistoryRepository` devem migrar para
  `SQLiteHistoryRepository`; o alias de compatibilidade permanece nesta release;
- ambientes que dependiam implicitamente de ONNX Runtime, LanceDB ou dos pacotes
  removidos precisam declará-los separadamente se ainda os utilizarem fora do
  runtime suportado.

## Benchmark de release

Em Windows com Python 3.11.0, perfil `demo`, modelos desabilitados e três repetições:

- pipeline sintético (`synthetic_pipeline_v1.json`, quatro casos): accuracy 1,0,
  macro-F1 1,0, latência média 7,60 ms e p95 16,50 ms;
- retrieval sintético (`synthetic_retrieval_v1.json`, seis casos, K=3): recall 1,0
  para as três variantes; o backend híbrido realmente carregado foi
  `tfidf+rapidfuzz-fallback`.

Os datasets são pequenos e sintéticos. Esses resultados são regressões de
engenharia, não uma medida de validade externa, equidade ou desempenho universal.
