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
