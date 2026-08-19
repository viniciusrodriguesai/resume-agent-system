# Configuração

Todas as opções da aplicação são centralizadas em `resume_ai.settings.Settings`.
Campos usam o prefixo `RESUME_`, não diferenciam maiúsculas de minúsculas e podem
vir do ambiente ou de um arquivo local `.env`. O arquivo `.env.example` contém um
ponto de partida sem segredos.

Precedência prática: argumentos explícitos de `Settings`, variáveis de ambiente,
`.env` e defaults do código. `Settings.for_profile` aplica defaults do perfil
somente aos campos que não foram definidos explicitamente.

## Perfis

| Campo | Padrão | Valores |
|---|---|---|
| `RESUME_PROFILE` | `demo` | `demo`, `balanced`, `complete` |
| `RESUME_ALLOWED_PROFILES` | todos | lista de perfis permitidos pela API |

| Perfil | Embedding | Backend | Reranker | Parser e PII | Top K |
|---|---|---|---|---|---|
| `demo` | MiniLM multilingual | Torch | não | parsers base e regex | 3 |
| `balanced` | multilingual-e5-small | Torch | top 3 | parsers base e regex | 4 |
| `complete` | BGE-M3 | Torch | BGE reranker top 5 | Docling e Presidio | 5 |

Perfis declaram intenção. Dependências e modelos continuam opcionais: falha de
carregamento aciona fallback e aparece em `engine_status`. O perfil demo tenta
embedding por padrão; para execução garantidamente lexical, defina
`RESUME_EMBEDDING_ENABLED=false`.

## Caminhos

| Campo | Padrão | Uso |
|---|---|---|
| `RESUME_PROJECT_ROOT` | raiz do pacote | base para caminhos relativos |
| `RESUME_DATA_DIR` | `data` | catálogo e SQLite |
| `RESUME_CACHE_DIR` | `.cache/resume-ai` | cache de modelos e resultados |

Caminhos relativos são resolvidos contra `project_root`. A construção de
`Settings` cria os diretórios de dados e cache se necessário. Em container, garanta
permissão de escrita para UID 10001.

## Matching e modelos

| Campo | Padrão | Observação |
|---|---|---|
| `RESUME_EMBEDDING_ENABLED` | `true` | permite tentativa de embedding |
| `RESUME_EMBEDDING_MODEL` | MiniLM multilingual | identificador Sentence Transformers |
| `RESUME_EMBEDDING_BACKEND` | `torch` | `onnx`, `torch` ou `openvino` |
| `RESUME_EMBEDDING_DEVICE` | `cpu` | dispositivo entregue à biblioteca |
| `RESUME_EMBEDDING_BATCH_SIZE` | 16 | tamanho de lote |
| `RESUME_NORMALIZE_EMBEDDINGS` | `true` | normaliza vetores |
| `RESUME_RERANKER_ENABLED` | `false` | habilita tentativa de CrossEncoder |
| `RESUME_RERANKER_MODEL` | mMARCO MiniLM | identificador do reranker |
| `RESUME_RERANKER_TOP_N` | 3 | candidatos reranqueados |
| `RESUME_TOP_K` | 3 | evidências recuperadas por requisito |
| `RESUME_MAX_REQUIREMENTS` | 30 | máximo extraído da vaga |
| `RESUME_MAX_CHUNK_CHARS` | 420 | tamanho aproximado de trecho |
| `RESUME_MAX_REVISIONS` | 1 | compatibilidade de configuração; não reexecuta o pipeline atual |

`RESUME_VECTOR_STORE` aceita `memory` ou `lancedb`, mas o fluxo de evidências
atual usa o `EmbeddingEngine` em memória. Selecionar LanceDB não muda o pipeline da
V6.

O perfil de dependências da V6 instala e valida Torch. `onnx` e `openvino`
permanecem valores aceitos para instalações gerenciadas pelo operador, mas seus
adaptadores não fazem parte de `requirements-ai.txt`. Se o backend solicitado não
carregar, o motor registra o fallback e continua pelo matching lexical.

## Parsing e privacidade

| Campo | Padrão | Observação |
|---|---|---|
| `RESUME_DOCLING_ENABLED` | `false` | tenta Docling antes dos parsers base |
| `RESUME_PRESIDIO_ENABLED` | `false` | complementa regex com Presidio |
| `RESUME_FULL_NER_ENABLED` | `false` | reservado; sem consumidor no pipeline atual |
| `RESUME_MAX_UPLOAD_MB` | 10 | limite antes do parser |
| `RESUME_MAX_DOCUMENT_CHARS` | 30.000 | currículo e extração de arquivo |
| `RESUME_MAX_JOB_CHARS` | 30.000 | descrição da vaga |
| `RESUME_ALLOWED_EXTENSIONS` | PDF, DOCX e TXT | extensões aceitas |
| `RESUME_STORE_RAW_DOCUMENTS` | `false` | metadado de política; runtime não persiste bruto |
| `RESUME_STORE_ANONYMIZED_DOCUMENTS` | `false` | consentimento exigido para cache em disco |

## Cache e histórico

| Campo | Padrão | Observação |
|---|---|---|
| `RESUME_CACHE_ENABLED` | `true` | habilita cache de resultados |
| `RESUME_CACHE_BACKEND` | `memory` | `memory` ou `disk` |
| `RESUME_CACHE_MAX_ENTRIES` | 128 | limite do cache em memória |
| `RESUME_CACHE_TTL_SECONDS` | 86.400 | validade de uma entrada |
| `RESUME_HISTORY_ENABLED` | `true` | habilita resumo SQLite |

`disk` sem `RESUME_STORE_ANONYMIZED_DOCUMENTS=true` é rejeitado durante a
configuração. O cache usa hash das entradas como chave, mas o valor contém o
`AnalysisResult` e pode incluir evidências anonimizadas.

O banco do histórico fica em `RESUME_DATA_DIR/history.sqlite3`. Desabilitar o
histórico evita inicialização e escrita do SQLite.

## API

| Campo | Padrão | Observação |
|---|---|---|
| `RESUME_ENVIRONMENT` | `development` | `development`, `test` ou `production` |
| `RESUME_API_KEY` | ausente | segredo do header `X-API-Key` |
| `RESUME_API_MAX_BODY_MB` | 1 | limite bruto de `POST /v1/analyze` |
| `RESUME_API_RATE_LIMIT_PER_MINUTE` | 60 | por cliente e processo; zero desabilita |
| `RESUME_CORS_ORIGINS` | Streamlit local | origens separadas por vírgula |

Em `production`, a análise retorna 503 se `RESUME_API_KEY` não estiver
configurada. Os demais endpoints permanecem públicos.

## Streamlit e login

| Campo | Padrão | Observação |
|---|---|---|
| `RESUME_REQUIRE_LOGIN` | `false` | exige sessão OIDC do Streamlit |

Segredos OIDC pertencem a `.streamlit/secrets.toml`, nunca ao `.env.example`.
Consulte [../AUTHENTICATION.md](../AUTHENTICATION.md).

## Logs

| Campo | Padrão | Observação |
|---|---|---|
| `RESUME_LOG_LEVEL` | `INFO` | nível do logger Python |
| `RESUME_LOG_PII` | `false` | compatibilidade; não habilita log de documentos |

O sanitizador continua obrigatório independentemente da configuração. Consulte
[OBSERVABILITY.md](OBSERVABILITY.md).

## Variáveis das bibliotecas

O exemplo também define variáveis que não pertencem a `Settings`:

- `HF_HOME`: diretório de cache do Hugging Face;
- `HF_HUB_OFFLINE`: impede acesso ao hub quando vale 1;
- `TOKENIZERS_PARALLELISM`: controla paralelismo dos tokenizers;
- `OMP_NUM_THREADS` e `MKL_NUM_THREADS`: limitam threads numéricas.

Essas variáveis são interpretadas pelas dependências e podem variar por plataforma.

## Configurações seguras por cenário

Execução lexical e efêmera para teste:

```dotenv
RESUME_ENVIRONMENT=test
RESUME_EMBEDDING_ENABLED=false
RESUME_RERANKER_ENABLED=false
RESUME_DOCLING_ENABLED=false
RESUME_PRESIDIO_ENABLED=false
RESUME_HISTORY_ENABLED=false
RESUME_CACHE_ENABLED=false
HF_HUB_OFFLINE=1
```

Execução local padrão:

```dotenv
RESUME_PROFILE=demo
RESUME_CACHE_BACKEND=memory
RESUME_HISTORY_ENABLED=true
RESUME_REQUIRE_LOGIN=false
```

Para rede, além da configuração da aplicação, use proxy com HTTPS, autenticação,
limites globais e proteção dos endpoints operacionais.

## Validação

Execute `python -m pytest tests/unit/test_settings.py` após mudar configuração.
Para inspecionar valores resolvidos, use `Settings().model_dump` excluindo
`api_key`. Mesmo sem a chave, a saída pode revelar caminhos locais: não a publique
e nunca imprima o conteúdo de `.env`.
