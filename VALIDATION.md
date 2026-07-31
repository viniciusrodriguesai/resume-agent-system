# Validação da V5.1

- todos os arquivos Python passaram por `compileall`;
- **10 testes passaram**;
- **1 teste visual foi ignorado** porque o Streamlit não está instalado no ambiente de validação;
- o fluxo completo foi executado com fallback local;
- evidências não contêm marcadores como `<EMAIL>`, `<TELEFONE>` ou `<NOME_CANDIDATO>`;
- requisito com Pandas, NumPy e Scikit-learn não recebe correspondência completa quando apenas uma competência aparece;
- embeddings são processados em lote e os trechos do currículo são reutilizados pelo cache da sessão;
- relatórios Markdown, JSON e CSV continuam sendo gerados;
- a API e os testes de integração permaneceram compatíveis.

Os modelos ONNX e o frontend Streamlit devem ser testados no computador de apresentação após a cópia do pacote.
