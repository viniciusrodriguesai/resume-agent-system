# Resume Match AI 6.0.6

Patch de bugfix da linha 6.0.x, limitado aos quatro achados reproduzíveis da
auditoria adversarial pós-release da 6.0.5. Não há mudança de arquitetura,
feature nova ou alteração de thresholds globais.

## CORREÇÕES CONFIRMADAS

- nomes reais continuam anonimizados quando estão próximos, contidos ou
  intercalados com spans de tecnologia; spans PERSON amplos são divididos para
  preservar somente a tecnologia realmente sobreposta;
- frases e documentos com múltiplas tecnologias mantêm a barreira de PII, sem
  confundir identificadores técnicos em PascalCase com nomes;
- falsos positivos PERSON do Presidio sobre verbos operacionais, incluindo
  `Trabalhei`, são descartados sem ocultar a pessoa real presente na mesma frase;
- a negação é limitada por ponto, exclamação, interrogação, ponto e vírgula,
  quebra de linha e boundary de bullet, sem contaminar uma alternativa OR
  positiva posterior;
- conceitos literais fora do catálogo, como AlphaDB, BetaDB, OmegaMQ e
  NovaCache, recebem os mesmos sinais de cobertura, operação, profissão,
  produção, teoria, superficialidade e negação aplicados às skills catalogadas;
- um literal com produção explícita pode satisfazer o requisito, enquanto uso
  local, estudo, skill list e negação continuam sem match de produção.

## REGRESSÕES COBERTAS

- casos determinísticos com Bruno Santos antes, depois e ao redor de Python,
  Kafka, Prometheus, FastAPI, PostgreSQL e múltiplas tecnologias;
- 500 combinações property-based de PERSON + TECH, TECH + PERSON e
  PERSON + TECH + TECH, com pessoa removida e tecnologia preservada;
- 150 combinações property-based de negação, cinco boundaries semânticos,
  OR/AND e reranker nos extremos 0,0 e 1,0;
- produção literal para AlphaDB, BetaDB, OmegaMQ e NovaCache, além dos controles
  local, estudo, skill list e negação;
- fixtures e invariantes das versões 6.0.3 a 6.0.5, incluindo zero coverage,
  AND/OR, intents, high volume, global rerank, headings, cache, formatos,
  documentos malformados e concorrência.

## COMPATIBILIDADE

- API FastAPI, Streamlit, modelos Pydantic, cache, histórico, formatos e perfis
  permanecem compatíveis;
- embeddings, reranker, Presidio e Docling continuam opcionais e lazy-loaded;
- dependências obrigatórias de runtime não foram alteradas;
- o suporte declarado permanece Python 3.11, 3.12 e 3.13.

## VALIDAÇÃO

- 511 testes aprovados e 2 ignorados na suíte completa pré-release;
- coverage comparável de 90,58%, acima dos 90,25% medidos na auditoria da
  6.0.5 com o mesmo escopo;
- 500 casos controlados executados com Microsoft Presidio real: zero vazamentos
  de pessoa, zero tecnologias removidas e zero falsos positivos do verbo
  operacional `Trabalhei`;
- mutation testing: 120 mutantes, 84 mortos, 36 sobreviventes, zero timeout e
  score de 70,00%;
- Ruff, mypy, avaliação semântica, `pip check` e auditorias runtime/dev
  aprovados;
- wheel, sdist, import limpo, API e Streamlit aprovados em Python 3.13;
- Docker Compose validado; runtime Docker não validado porque o daemon local
  estava indisponível;
- CI aprovado em Python 3.11, 3.12 e 3.13.
