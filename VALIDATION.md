# Validation evidence

## Portfolio audit — 2026-10-01

Local environment: Linux, Python 3.12.14, NumPy 2.2.4; optional embedding and reranking models disabled. Dependency versions and results describe this environment, not all installations.

- Test suite: 511 passed, 2 skipped after the dependency bound change (11.92 seconds).
- Ruff passed during the audit.
- Mypy: no issues in 62 source files with the default Python 3.11 target after selecting NumPy 2.2.4. NumPy 2.5.3 had introduced Python 3.12 syntax in dependency stubs that this target could not parse.
- A three-run lexical pipeline benchmark completed on four synthetic cases. Perfect scores on this tiny internal fixture are not evidence of generalization; no real-applicant accuracy claim is made.

Large optional models, Docker deployment, real-world hiring outcomes, fairness and probability calibration were not validated. The two skipped tests do not count as passed checks.

## Historical V5.2 evidence

The following section is preserved for historical context and does not describe the current suite:

# Validação da V5.2

- todos os arquivos Python passaram por `compileall`;
- **12 testes passaram**, incluindo o teste de inicialização do Streamlit;
- o fluxo completo foi executado com fallback local;
- a nova escala de compatibilidade foi testada nos cinco níveis;
- requisitos obrigatórios e desejáveis ausentes são contabilizados separadamente;
- evidências não contêm marcadores como `<EMAIL>`, `<TELEFONE>` ou `<NOME_CANDIDATO>`;
- requisito com Pandas, NumPy e Scikit-learn não recebe correspondência completa quando apenas uma competência aparece;
- embeddings são processados em lote e os trechos do currículo são reutilizados pelo cache da sessão;
- relatórios Markdown, JSON e CSV continuam sendo gerados;
- a API e os testes de integração permaneceram compatíveis.

O lint com Ruff não foi executado neste ambiente porque a ferramenta não estava instalada. A configuração do projeto e o workflow de CI permanecem disponíveis para essa verificação no ambiente de desenvolvimento e no GitHub Actions.

Os modelos ONNX devem ser testados no computador ou no ambiente de hospedagem após a cópia do pacote.
