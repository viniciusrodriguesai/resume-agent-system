# Arquitetura V5

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
                                                cache seguro + histórico mínimo
```

O serviço de aplicação não importa Streamlit nem FastAPI. Isso permite trocar a interface sem reescrever o pipeline.
