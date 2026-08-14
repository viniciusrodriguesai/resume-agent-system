# Arquitetura V5.2.1

```text
Streamlit ─┐
           ├─> ResumeAnalysisService ─> Privacy Agent ─> Candidate/Job Agents
FastAPI ───┘                                  │
                                              └─> Evidence Engine
                                                   ├─ lexical/fuzzy
                                                   ├─ embeddings ONNX opcional
                                                   └─ reranker opcional
                                                         │
                                      Scoring ─> Review ─> Recommendations ─> Reports
                                                         │
                                                cache em memória + histórico mínimo
```

O serviço de aplicação não importa Streamlit nem FastAPI. Isso permite trocar a interface sem reescrever o pipeline.


O motor de evidências codifica os trechos do currículo uma única vez, processa as consultas em lote e reutiliza embeddings durante a sessão.

`resume_ai` é a única implementação canônica. As antigas árvores `agents`, `services` e `resume_v4` foram removidas para evitar comportamentos divergentes.

## Limites de confiança

- o cache de resultados usa memória por padrão;
- persistência em disco exige consentimento explícito para armazenar texto anonimizado;
- cada requisição recebe um novo ID, mesmo quando reutiliza cálculo em cache;
- perfis e tamanhos de entrada são limitados pelo deployment;
- histórico SQLite guarda somente resumo, pontuação e telemetria.
