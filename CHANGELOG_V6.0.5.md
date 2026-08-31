# Resume Match AI 6.0.5

Patch de estabilização da linha 6.0.x. Esta versão corrige a aplicação dos níveis
de intenção de requisitos, a fronteira de cobertura zero e a proteção de termos
técnicos no Presidio, sem alterar arquitetura, thresholds globais, agentes,
frontend ou dependências obrigatórias.

## CORREÇÕES CONFIRMADAS

- `KNOWLEDGE`, `EXPERIENCE`, `PROFESSIONAL_EXPERIENCE` e
  `PRODUCTION_EXPERIENCE` agora possuem contratos distintos na política final;
- skill list isolada é aceita para conhecimento, mas não comprova experiência
  aplicada, profissional ou em produção;
- projeto pessoal pode comprovar uso aplicado normal, mas não experiência
  profissional ou produção;
- evidência profissional exige contexto profissional explícito, e produção exige
  contexto produtivo real, com campos tipados de contexto disponíveis em cada
  candidato de evidência;
- cobertura de conceitos igual a zero, sem regra semântica determinística, fica
  estritamente abaixo do menor threshold parcial em todos os níveis de rigor;
- a exceção determinística de alto volume quantificado continua podendo produzir
  evidência parcial com `semantic_rule_match=true`;
- resultados PERSON do Presidio agora são comparados com spans técnicos absolutos,
  preservando nomes reais na mesma linha e protegendo somente o termo técnico
  sobreposto;
- spans PERSON amplos são recortados ao redor de tecnologias, mantendo PII
  anonimizada sem apagar tecnologias legítimas.

## REGRESSÕES COBERTAS

- intents de conhecimento, experiência, experiência profissional e produção com
  reranker adversarial entre 0,0 e 1,0;
- fixtures profissionais e exclusivamente pessoais em `balanced + equilibrado` e
  `complete + conservador`;
- cobertura zero para SINGLE, AND, OR e conceito literal desconhecido;
- Prometheus, João Prometheus Silva, João Silva com Python, Maria Kafka com
  FastAPI, Kafka Oliveira com PostgreSQL e pessoa com AlphaDB;
- model safety, headings, AND/OR, negação, evidência teórica, high volume, ranking,
  cache e equivalência TXT/DOCX/PDF das versões 6.0.3 e 6.0.4.

## COMPATIBILIDADE

- API FastAPI, Streamlit, JSON, CSV, Markdown, cache, histórico, perfis e defaults
  de privacidade permanecem compatíveis;
- embeddings, reranker, Docling e Presidio continuam opcionais e lazy-loaded;
- o fallback lexical continua determinístico e offline;
- o suporte declarado permanece Python 3.11, 3.12 e 3.13;
- `raw_document_stored=false` e `anonymized_document_stored=false` permanecem os
  defaults.

## VALIDAÇÃO

- 446 testes aprovados e cobertura total de 92%, acima da baseline 91,32%;
- validações reais offline com E5/MMARCO e BGE-M3/BGE-reranker, além do Presidio;
- Ruff, mypy, `pip check` e auditorias runtime/dev aprovados;
- sdist, wheel, import, API, Streamlit e Docker Compose validados;
- runtime Docker não validado porque o daemon local estava indisponível.
