# Technical Basis

The implementation follows these official project patterns:

- LangGraph `StateGraph`, `START`, `END`, and conditional routing:
  https://docs.langchain.com/oss/python/langgraph/overview
- Sentence Transformer embeddings followed by CrossEncoder reranking:
  https://www.sbert.net/
- Docling `DocumentConverter` and Markdown export:
  https://docling-project.github.io/docling/getting_started/quickstart/
- Streamlit `st.cache_resource` for model/resource caching:
  https://docs.streamlit.io/develop/api-reference/caching-and-state/st.cache_resource
- ESCO downloadable classifications:
  https://esco.ec.europa.eu/en/use-esco/download
- GitHub Actions Python testing:
  https://docs.github.com/actions/automating-builds-and-tests/building-and-testing-python
- NIST AI Risk Management Framework:
  https://www.nist.gov/itl/ai-risk-management-framework

## Suggested academic experiment

1. Create at least 200 manually labeled requirement/evidence pairs.
2. Compare lexical fallback against multilingual embeddings.
3. Compare embeddings against embeddings plus CrossEncoder.
4. Report accuracy, precision, recall, macro F1, processing time, and errors by
   language.
5. Discuss false positives, false negatives, bias, and document parsing errors.
