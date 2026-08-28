# Resume Match AI 6.0.4

Patch de bugfix e hardening da linha 6.0.x. Esta versão subordina embeddings e
CrossEncoder às invariantes semânticas determinísticas, sem alterar arquitetura,
thresholds globais, agentes, frontend ou dependências obrigatórias.

## CONFIRMED FIXES

- candidatos sem cobertura de conceitos explícitos nunca podem virar match, mesmo
  com saída extrema do reranker;
- ceilings de negação, menção superficial, conhecimento teórico e AND incompleto,
  assim como floors operacionais e de escala quantificada, são reaplicados após o
  reranking em todo o pool de candidatos;
- uma alternativa OR operacional válida não pode ser derrubada pelo modelo, e AND
  incompleto nunca se torna match completo;
- todos os candidatos são reordenados globalmente pelo score final com desempate
  determinístico, inclusive quando `reranker_top_n` é menor que o pool;
- o retrieval preserva evidências determinísticas relevantes antes do corte final,
  incluindo conceitos exatos, operação, escala, negação e contexto superficial;
- classes de força mantêm produção acima de uso operacional, listagem, estudo e
  negação, limitando o reranker a comparar evidências semanticamente compatíveis;
- o Presidio preserva tecnologias conhecidas e conceitos técnicos literais em
  contexto técnico, sem desativar a anonimização de nomes reais;
- explicações refletem cobertura, negação, superficialidade, teoria, AND/OR,
  operação e fallback literal reais, sem afirmar conceitos ausentes.

## COMPATIBILITY

- todos os fixes da 6.0.3 foram preservados;
- API FastAPI, Streamlit, modelos Pydantic públicos, JSON, CSV, Markdown, cache,
  histórico, perfis, rigor e defaults de privacidade continuam compatíveis;
- embeddings, reranker, Docling e Presidio permanecem opcionais e lazy-loaded;
- o fallback lexical continua determinístico, offline e sem download de modelos;
- o suporte declarado permanece Python 3.11, 3.12 e 3.13.

## VALIDATION

- 386 testes aprovados, com cobertura de `resume_ai` em 91,32%;
- regressões adversariais com reranker mockado nos extremos de 0,0 a 1,0;
- fixtures reais `balanced + equilibrado` e `complete + conservador` aprovadas com
  embeddings e rerankers locais carregados e zero matches com cobertura zero;
- Ruff, mypy, `pip check` e auditorias de dependências aprovados;
- equivalência TXT/DOCX/PDF e identidade semântica de cache preservadas;
- Docker Compose validado; runtime Docker não validado por daemon indisponível.
