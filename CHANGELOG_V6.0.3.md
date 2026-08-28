# Resume Match AI 6.0.3

Patch de hardening semântico da linha 6.0.x. Esta versão corrige defeitos
generalizáveis observados após a validação manual da 6.0.2, sem introduzir nova
arquitetura, agentes, frontend, LLM ou dependências obrigatórias de IA.

## CONFIRMED FIXES

- headings e subheadings curtos, não-bullet e seguidos por bullets são reconhecidos
  estruturalmente em português, inglês, Title Case, caixa alta e Unicode;
- a prioridade da seção e o label da subseção são mantidos separadamente, evitando
  que headings arbitrários virem requisitos sem perder a prioridade obrigatória da
  seção pai;
- conceitos literais fora do catálogo, como tecnologias novas ou expressões de
  domínio, participam da cobertura quando extraídos de qualificadores conservadores;
- grupos tipados `Concept`/`ConceptGroup` preservam todas as alternativas AND/OR,
  inclusive quando parte ou todos os conceitos não existem no catálogo;
- aliases curtos contidos em nomes canônicos não podem contornar contexto de
  negação, estudo ou leitura do alias mais específico;
- requisitos distinguem intenção de conhecimento, experiência, experiência
  profissional e experiência em produção; uso operacional ranqueia acima de uma
  listagem isolada sem alterar pesos ou thresholds globais;
- o parser de currículo respeita seções explícitas de experiência, projetos e
  formação antes de aplicar heurísticas lexicais, sem duplicar experiência como
  projeto e sem truncar prematuramente um segundo emprego;
- Apache Kafka, Prometheus, Grafana, Memcached, Pulumi e Java foram adicionados ao
  catálogo estruturado com aliases e categorias, preservando fronteiras como
  `Java != JavaScript` e `Git != GitHub`;
- cache hits mantêm a política de novo ID, regeneram o Markdown com essa identidade
  e distinguem timings atuais dos timings da execução original cacheada;
- explicações de evidência agora descrevem sinais reais de operação, negação,
  superficialidade, cobertura AND/OR e fallback literal de forma determinística;
- resultados do Presidio Analyzer são convertidos explicitamente para o tipo
  esperado pelo Presidio Anonymizer, removendo a incompatibilidade de tipagem sem
  tornar a dependência opcional obrigatória.

## COMPATIBILITY

- API FastAPI, Streamlit, modelos públicos, JSON, CSV, Markdown, histórico, privacy
  e perfis existentes permanecem backward-compatible;
- embeddings, reranker, Docling e Presidio continuam opcionais e carregados de
  forma preguiçosa;
- o fallback lexical permanece determinístico, offline e sem download de modelos;
- o suporte declarado permanece Python 3.11, 3.12 e 3.13.

## VALIDATION

- fixture sintética 6.0.3 aprovada com 17 requisitos reais, 13 obrigatórios e 4
  desejáveis nos rigores flexível, equilibrado e conservador;
- 360 testes aprovados e cobertura de `resume_ai` em 90%;
- Ruff, mypy e `pip check`: aprovados;
- `pip-audit` de runtime e desenvolvimento: nenhuma vulnerabilidade conhecida;
- build de sdist/wheel, smoke do wheel, API e Streamlit: validados na preparação da
  release;
- Docker Compose: configuração válida;
- Docker runtime: não validado porque o daemon não estava disponível.
