# Observabilidade

A V6 oferece logs estruturados, correlação, tempos por estágio, estado de backends e
métricas opcionais. O desenho prioriza diagnóstico sem copiar currículo, vaga,
evidências ou mensagens arbitrárias para logs.

## Identificadores de correlação

Cada análise executa dentro de um `correlation_scope`. Na API, o cliente pode enviar
`X-Request-ID`; valores válidos:

- começam por letra ou número;
- usam apenas letras, números, ponto, sublinhado e hífen;
- têm no máximo 64 caracteres.

Um valor ausente ou inválido é substituído por UUID hexadecimal local. A resposta
inclui `X-Request-ID`, e o mesmo identificador aparece nos eventos do pipeline. A
propagação usa `ContextVar`, evitando compartilhar o valor entre requisições
concorrentes.

O `analysis_id` identifica um resultado de negócio. O `correlation_id` liga eventos
da execução. Eles não são equivalentes: inclusive um cache hit recebe novo
`analysis_id`.

## Logs JSON

`Telemetry` instala um único handler no logger `resume_ai` e produz um objeto JSON
compacto por linha. Campos base:

- `timestamp` UTC;
- `level`;
- `logger`;
- `event`;
- campos operacionais sanitizados.

Eventos principais:

| Evento | Quando |
|---|---|
| `agent_completed` | estágio termina com sucesso ou warning |
| `agent_failed` | executor captura falha de agente |
| `analysis_completed` | serviço conclui, inclusive por cache |
| `analysis_failed` | validação ou pipeline falha |
| `api_unhandled_error` | adaptador captura exceção inesperada |

Os eventos de agente registram estágio, nome, status, duração, confiança e contagens
de warnings e evidências. A conclusão registra perfil, score, duração e cache hit.
Falhas registram somente estágio e nome da classe da exceção, nunca `str(exc)` ou
traceback no payload público.

## Sanitização e PII

O sanitizador aceita somente campos enumerados em
`resume_ai/infrastructure/log_sanitizer.py`. Campos desconhecidos são descartados.
Valores não escalares são redigidos. Strings acima de 128 caracteres, e-mails e
telefones são substituídos por `[REDACTED]`; quebras de linha são removidas.

Nomes de evento também usam allowlist sintática e limite de 64 caracteres. Um evento
inválido se torna `invalid_event`.

`RESUME_LOG_PII` existe na configuração por compatibilidade, mas o pipeline atual
não abre um caminho para conteúdo pessoal nos logs. Não use esse campo como
autorização para registrar documentos.

## Tempos e diagnóstico por agente

O serviço mede com relógio monotônico:

- privacidade;
- estruturação do currículo;
- estruturação da vaga;
- recuperação de evidências;
- scoring;
- revisão;
- recomendações;
- relatório;
- total.

Cada `AgentResult` também contém `duration_ms`, `confidence`, `status`,
`warnings`, referências de evidência e metadados limitados ao estágio. Esses dados
são exibidos no Streamlit e retornados no `AnalysisResult`.

O estado do motor informa configuração e carregamento real de embedding e reranker,
erros de backend e número de entradas do cache de embeddings. Erros podem conter
detalhes técnicos de biblioteca e devem ser tratados como diagnóstico local, não
como mensagem pública para usuários não confiáveis.

## Métricas

Quando `prometheus-client` está instalado, `GET /metrics` expõe:

| Métrica | Tipo | Labels | Significado |
|---|---|---|---|
| `resume_ai_analysis_total` | Counter | `profile`, `status` | análises concluídas ou falhas |
| `resume_ai_analysis_duration_seconds` | Histogram | `profile` | duração total de sucesso sem cache |
| `resume_ai_last_score` | Gauge | `profile` | último score observado no processo |
| `resume_ai_cache_total` | Counter | `profile`, `result` | hits e misses do cache |

Sem essa dependência opcional, o endpoint continua disponível e retorna apenas
`resume_ai_process_memory_mb`, calculado a partir do RSS atual.

```bash
curl http://127.0.0.1:8000/metrics
```

As métricas são locais ao processo. Reinício zera séries em memória; múltiplos
workers não agregam valores. O gauge de score não contém texto, mas ainda é dado
operacional potencialmente sensível e não deve ser publicado sem controle de acesso.

## Saúde e readiness

- `GET /health` cria ou reutiliza o serviço do perfil padrão e responde
  `status=ok`;
- `GET /ready` responde `status=ready` quando a composição do serviço funciona e
  retorna 503 quando ela falha.

Ambos informam versão, perfil, se o embedding já está carregado e memória RSS. O
modelo pode carregar de forma preguiçosa apenas na primeira análise; portanto
`model_loaded=false` não significa necessariamente indisponibilidade.

O readiness atual verifica construção do serviço, não faz inferência de modelo, I/O
de SQLite nem download. Use probes adicionais no ambiente se esses recursos forem
obrigatórios.

## Operação local

Defina `RESUME_LOG_LEVEL=INFO` ou outro nível aceito pelo módulo `logging`.

Execute a API com:

```bash
python -m uvicorn api.main:app --host 127.0.0.1 --port 8000
```

Na investigação de uma falha, procure primeiro por `X-Request-ID` ou
`correlation_id`, depois compare `stage`, `error_type` e eventos anteriores. Não
adicione o conteúdo do currículo para facilitar troubleshooting; reproduza com dados
sintéticos.

## Limitações e evolução

- não há exportador OpenTelemetry conectado ao pipeline;
- `structlog` e pacotes OpenTelemetry são opcionais, mas o runtime atual usa
  `logging` padrão e métricas Prometheus;
- não há tracing distribuído porque a V6 é um processo local sem workers;
- métricas e logs não têm retenção própria;
- `/metrics` é público na aplicação e deve ser protegido pelo deployment;
- duração de cache hit é registrada como zero pelo serviço e não mede toda a latência
  HTTP percebida;
- o histórico SQLite é armazenamento de resultados resumidos, não backend de
  telemetria.

Qualquer integração futura deve preservar a allowlist de campos e a proibição de
documentos, evidências e mensagens de exceção nos eventos.
