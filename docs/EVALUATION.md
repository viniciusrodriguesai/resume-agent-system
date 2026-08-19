# Avaliação e benchmarks

A V6 possui um framework local e reproduzível para avaliar classificação,
recuperação e o pipeline completo. Os datasets versionados são sintéticos; nenhum
currículo real deve ser adicionado a fixtures ou resultados.

Os scripts não publicam uma afirmação universal de qualidade. Métricas de latência e
memória dependem de hardware, sistema operacional, versões instaladas, modelos já
baixados e aquecimento do processo.

## Estrutura

- `evaluation/datasets/synthetic_retrieval_v1.json`: consultas, candidatos e IDs
  relevantes para ranking.
- `evaluation/datasets/synthetic_pipeline_v1.json`: currículo, vaga e status
  esperado por requisito para o fluxo completo.
- `evaluation/schema.py`: schemas estritos Pydantic, com campos extras proibidos,
  limites e validação de IDs.
- `evaluation/metrics`: Precision, Recall, F1, Precision@K, Recall@K, MRR, NDCG@K,
  média, p95 e delta estimado de memória RSS.
- `evaluation/benchmarks`: runners independentes de CLI.
- `scripts/benchmark_retrieval.py`: compara TF-IDF, RapidFuzz e o ranker híbrido.
- `scripts/benchmark_pipeline.py`: mede o serviço completo e os oito agentes.
- `scripts/evaluate.py`: regressão pequena de classificação usada pelo CI.

## Métricas

No benchmark de recuperação:

- **Precision** mede quantos candidatos marcados como recuperados no top K são
  relevantes, considerando todos os candidatos dos casos;
- **Recall** mede quantos relevantes foram recuperados no top K;
- **F1** é a média harmônica de Precision e Recall;
- **Precision@K** é a fração das K posições ocupada por relevantes;
- **Recall@K** é a fração de todos os relevantes presente nas K primeiras posições;
- **MRR** usa o inverso da posição do primeiro relevante e calcula a média por caso;
- **NDCG@K** desconta acertos por posição e normaliza pela ordenação ideal, com
  relevância binária.

O benchmark do pipeline compara os rótulos `matched`, `partial` e `missing` por
requisito e reporta métricas de classificação agregadas, incluindo macro F1.

Os dois runners medem latência média e p95 com `time.perf_counter`. A memória é o
maior aumento observado de RSS do processo em relação ao início; não é consumo total,
heap isolado nem limite garantido.

## Benchmark de recuperação

Execução lexical, sem download de modelos:

```bash
python scripts/benchmark_retrieval.py --runs 3 --k 3
```

Essa execução compara `tfidf`, `rapidfuzz` e `hybrid-fallback`. Para tentar
embeddings e reranker configurados:

```bash
python scripts/benchmark_retrieval.py --runs 3 --k 3 --include-models
```

Para preservar o relatório:

```bash
python scripts/benchmark_retrieval.py --output build/benchmark-retrieval.json
```

O JSON inclui versão de schema, data UTC, SHA-256 e número de casos do dataset,
Python, plataforma, parâmetros, métricas, desempenho e `backend_status`. Confirme
`actual_backend`, `embedding_loaded` e `reranker_loaded` antes de atribuir um
resultado a modelos: falhas usam fallback lexical e ficam registradas.

## Benchmark do pipeline completo

Execução determinística sem modelos e sem cache ou histórico:

```bash
python scripts/benchmark_pipeline.py --profile demo --runs 3
```

Execução que tenta os modelos do perfil escolhido:

```bash
python scripts/benchmark_pipeline.py --profile balanced --runs 3 --include-models
```

O relatório contém as métricas por requisito, desempenho, duração média por agente e
estado real dos backends. O runner falha se o conjunto de requisitos produzido não
corresponder aos labels ou se os rótulos mudarem entre repetições.

## Regressão usada no CI

```bash
python scripts/evaluate.py --min-accuracy 0.95 --min-macro-f1 0.90
```

Sem `--full-ai`, esse comando avalia o caminho local lexical sobre
`examples/evaluation_labels.csv`. O job `quality` do GitHub Actions usa os limiares
acima. Com `--full-ai`, o script tenta embedding e reranker locais; disponibilidade
de modelos deve ser confirmada separadamente.

## Testes do framework

```bash
python -m pytest tests/evaluation tests/test_evaluation.py tests/test_quality_regression.py
```

Os testes cobrem fórmulas, validação dos schemas, determinismo, rankers e runners. Eles
provam comportamento do framework e regressões conhecidas; não substituem um dataset
representativo do uso pretendido.

## Reproduzindo e comparando resultados

Para uma comparação válida:

1. use o mesmo commit e registre `git rev-parse HEAD`;
2. use o mesmo dataset e confirme o SHA-256 emitido;
3. fixe `--runs`, `--k`, perfil e `--include-models`;
4. registre Python, plataforma, CPU, memória e estado de energia;
5. confirme o backend real no JSON, não apenas a variante solicitada;
6. separe primeira execução, que pode carregar modelos, de execuções aquecidas;
7. não compare números de máquinas diferentes como se fossem equivalentes;
8. preserve o JSON bruto antes de elaborar tabelas ou conclusões.

Os runners desabilitam cache e histórico para evitar que reuso de resultado ou I/O de
SQLite distorça a medição do pipeline. Cada variante deve produzir o mesmo ranking ou
os mesmos rótulos em todas as repetições; divergência encerra o benchmark com erro.

## Novos datasets

Use apenas dados sintéticos ou comprovadamente anonimizados. Cada caso deve declarar
`data_origin`. IDs precisam ser únicos e labels devem referenciar candidatos
existentes. Para pipeline, o texto do requisito no label precisa normalizar para o
mesmo texto produzido pelo agente de vaga.

Antes de aceitar um dataset:

- faça revisão humana independente dos labels;
- verifique diversidade de idioma, formato, senioridade e domínio;
- inclua negativos difíceis, negações e requisitos cumulativos;
- procure PII residual e segredos;
- versione o dataset quando os labels mudarem;
- registre limitações e critérios de exclusão.

O dataset sintético atual é pequeno e voltado a regressão de engenharia. Ele não
mede representatividade populacional, validade externa, calibração por grupo ou
equidade de contratação.

## Interpretação responsável

Um score melhor no dataset local não autoriza decisão automática sobre pessoas.
Matching lexical pode favorecer formulações idênticas; embeddings podem reproduzir
vieses do modelo; labels humanos também podem conter viés. Avalie erros por categoria
e inspecione evidências, não apenas uma média agregada.

Não há benchmark público entre modelos nem avaliação sistemática de viés concluídos
na V6. Esses itens permanecem trabalho futuro e não devem ser apresentados como
resultados existentes.
