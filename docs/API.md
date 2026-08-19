# API FastAPI

A API expõe o mesmo `ResumeAnalysisService` usado pelo Streamlit. Ela é destinada a
execução local ou atrás de um gateway controlado; não inclui TLS, usuários, papéis ou
rate limiting distribuído.

## Inicialização

```bash
python -m uvicorn api.main:app --host 127.0.0.1 --port 8000
```

Documentação gerada pelo FastAPI:

- Swagger UI: `http://127.0.0.1:8000/docs`;
- OpenAPI JSON: `http://127.0.0.1:8000/openapi.json`.

## Endpoints

| Método | Rota | Autenticação | Resposta |
|---|---|---|---|
| GET | `/health` | pública | liveness, versão, perfil, modelo e RSS |
| GET | `/ready` | pública | readiness da composição do serviço |
| GET | `/v1/profiles` | pública | perfis permitidos e descrições |
| POST | `/v1/analyze` | `X-API-Key` quando configurada | `AnalysisResult` |
| GET | `/metrics` | pública | Prometheus ou gauge RSS mínimo |

## Análise

`POST /v1/analyze` recebe JSON com:

| Campo | Tipo | Padrão | Limite |
|---|---|---|---|
| `resume_text` | string | obrigatório | 10 a 100.000 no schema; 30.000 no serviço por padrão |
| `job_text` | string | obrigatório | 10 a 100.000 no schema; 30.000 no serviço por padrão |
| `profile` | enum | `demo` | `demo`, `balanced` ou `complete` |
| `strictness` | enum | `equilibrado` | `flexível`, `equilibrado` ou `conservador` |

O perfil também precisa estar em `RESUME_ALLOWED_PROFILES`. O limite HTTP padrão é
`RESUME_API_MAX_BODY_MB=1` e é aplicado antes da desserialização, inclusive quando
o corpo chega em chunks.

Exemplo usando um arquivo JSON local sintético:

```bash
curl -X POST -H Content-Type:application/json --data-binary @request.json http://127.0.0.1:8000/v1/analyze
```

Quando `RESUME_API_KEY` está configurada, acrescente o header `X-API-Key`. Em
produção, ausência de chave configurada causa HTTP 503 no endpoint de análise.

## Resposta de análise

`AnalysisResult` inclui:

- `analysis_id`, `created_at`, perfil e rigor;
- perfil estruturado e anonimizado do candidato;
- vaga estruturada e requisitos;
- relatório de privacidade;
- evidência e scores por requisito;
- score geral, categorias, limiares e explicações;
- recomendações e resumo do revisor;
- oito `AgentResult` com status, duração, confiança, warnings e metadados;
- estado real de embedding, reranker e cache;
- tempos por estágio;
- relatório Markdown.

A resposta pode conter trechos anonimizados do currículo e detalhes da vaga. Trate-a
como dado sensível, não a registre em proxies e respeite `Cache-Control: no-store`.

## Perfis

`GET /v1/profiles` retorna somente perfis habilitados no deployment. As descrições
refletem as configurações padrão:

- `demo`: MiniLM ONNX, sem reranker e sem Docling;
- `balanced`: E5-small ONNX e reranker no top 3;
- `complete`: BGE-M3, BGE reranker, Docling e Presidio quando instalados.

Modelos carregam de forma preguiçosa. Se uma dependência ou modelo estiver
indisponível, o motor pode usar fallback lexical; confira `engine_status`.

## Erros públicos

Erros usam o envelope:

```text
error
  code: identificador_estável
  message: mensagem segura
  request_id: correlação da requisição
```

O servidor não retorna mensagem de exceção, traceback, caminho local ou conteúdo do
documento. Principais status:

| HTTP | Situação |
|---|---|
| 400 | `Content-Length` inválido ou requisição malformada |
| 401 | API key ausente ou incorreta |
| 403 | perfil não permitido |
| 413 | corpo acima do limite |
| 422 | JSON, schema ou limite de texto inválido |
| 429 | limite por minuto excedido |
| 500 | falha interna inesperada |
| 503 | serviço indisponível ou chave obrigatória não configurada |

O handler converte detalhes internos de `HTTPException` para mensagens públicas
padronizadas. Use `error.code` para lógica de cliente e `request_id` para
diagnóstico; não dependa do texto em português.

## Correlação

O cliente pode enviar `X-Request-ID`. Valores inválidos são substituídos, não
refletidos. A resposta devolve o identificador efetivo no mesmo header e no envelope
de erro.

Caracteres aceitos: letras, números, ponto, sublinhado e hífen, até 64 caracteres,
começando por letra ou número.

## Rate limiting

`RESUME_API_RATE_LIMIT_PER_MINUTE` limita `POST /v1/analyze` por endereço visto
pelo processo. Valor zero desabilita o limitador.

O controle usa memória local:

- reinício perde o estado;
- múltiplos workers têm contadores separados;
- não há coordenação entre réplicas;
- o endereço depende da configuração correta do proxy;
- a tabela de clientes não tem política global de retenção.

Em deployment distribuído, aplique o limite autoritativo no gateway.

## CORS e headers

`RESUME_CORS_ORIGINS` é uma lista separada por vírgulas. O padrão permite apenas
Streamlit em localhost e loopback. Credenciais CORS ficam desabilitadas; métodos
permitidos são GET e POST.

Respostas recebem:

- `X-Content-Type-Options: nosniff`;
- `X-Frame-Options: DENY`;
- `Referrer-Policy: no-referrer`;
- `Permissions-Policy` sem câmera, geolocalização ou microfone;
- `Cache-Control: no-store` na análise;
- `X-Request-ID`.

HSTS não é definido porque a aplicação não termina TLS. Configure HTTPS e HSTS no
proxy que realmente controla a conexão segura.

## Saúde e readiness

`/health` e `/ready` retornam `HealthResponse` com status, versão, perfil,
`model_loaded` e RSS. O modelo é lazy; `model_loaded=false` pode ser normal antes
da primeira inferência.

`/ready` verifica se o serviço pode ser construído. Não prova download ou inferência
do modelo, escrita SQLite, espaço em disco ou conectividade externa. Os healthchecks
do Docker usam readiness para a API e o endpoint interno de saúde do Streamlit.

## Compatibilidade

A API segue a versão do pacote. Mudanças compatíveis podem acrescentar campos; os
modelos de resultado ignoram campos extras ao ler cache legado, mas clientes HTTP
devem tolerar adições. Alterações incompatíveis exigem nova rota versionada além de
`/v1`.
