# Fundamentação técnica

Este documento reúne referências oficiais relacionadas às decisões da V6. Elas
explicam as técnicas; não provam que todo recurso citado esteja ativo. A fonte de
verdade do runtime é o código e os guias de arquitetura e configuração.

## Recuperação e reranking

- Sentence Transformers, semantic search:
  https://www.sbert.net/examples/sentence_transformer/applications/semantic-search/README.html
- Sentence Transformers, retrieve and rerank:
  https://www.sbert.net/examples/sentence_transformer/applications/retrieve_rerank/README.html
- CrossEncoder:
  https://www.sbert.net/examples/cross_encoder/applications/README.html
- scikit-learn, TF-IDF:
  https://scikit-learn.org/stable/modules/feature_extraction.html#text-feature-extraction
- RapidFuzz:
  https://rapidfuzz.github.io/RapidFuzz/

A V6 segue o padrão de recuperar candidatos antes de aplicar CrossEncoder, mas
combina scores próprios de TF-IDF, RapidFuzz, cobertura de conceitos e embedding.
Pesos, boosts, negação e fallback são regras do projeto, não defaults das bibliotecas.

## Modelos configurados

- MiniLM multilingual:
  https://huggingface.co/sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
- multilingual-e5-small:
  https://huggingface.co/intfloat/multilingual-e5-small
- BGE-M3:
  https://huggingface.co/BAAI/bge-m3
- mMARCO MiniLM reranker:
  https://huggingface.co/cross-encoder/mmarco-mMiniLMv2-L12-H384-v1
- BGE reranker v2 M3:
  https://huggingface.co/BAAI/bge-reranker-v2-m3

Licença, revisão, integridade e disponibilidade de cada modelo devem ser verificadas
antes de deployment. O repositório não fixa os artefatos de modelo por hash.

## Documentos e anonimização

- pypdf:
  https://pypdf.readthedocs.io/
- python-docx:
  https://python-docx.readthedocs.io/
- Docling:
  https://docling-project.github.io/docling/getting_started/quickstart/
- Microsoft Presidio:
  https://microsoft.github.io/presidio/anonymizer/
- formato Open Packaging Conventions:
  https://learn.microsoft.com/openspecs/office_standards/ms-opc/

Docling e Presidio são opcionais. A V6 mantém parsers base e regex locais. Validação
estrutural reduz abuso, mas não transforma bibliotecas de parsing em sandbox.

## Aplicação e interfaces

- Pydantic Settings:
  https://docs.pydantic.dev/latest/concepts/pydantic_settings/
- FastAPI middleware:
  https://fastapi.tiangolo.com/tutorial/middleware/
- FastAPI error handling:
  https://fastapi.tiangolo.com/tutorial/handling-errors/
- FastAPI testing:
  https://fastapi.tiangolo.com/tutorial/testing/
- Streamlit resource cache:
  https://docs.streamlit.io/develop/api-reference/caching-and-state/st.cache_resource
- Streamlit AppTest:
  https://docs.streamlit.io/develop/api-reference/app-testing/st.testing.v1.apptest
- Streamlit OIDC:
  https://docs.streamlit.io/develop/concepts/connections/authentication

O login Streamlit verifica autenticação OIDC, não autorização por papel. O cache de
recursos compartilha serviços por perfil e requer que os objetos sejam seguros para
uso concorrente.

## Segurança e risco

- OWASP File Upload Cheat Sheet:
  https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html
- OWASP Logging Cheat Sheet:
  https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html
- NIST AI Risk Management Framework:
  https://www.nist.gov/itl/ai-risk-management-framework
- NIST Privacy Framework:
  https://www.nist.gov/privacy-framework

Essas referências orientam minimização, validação, observabilidade segura e revisão
humana. O projeto não declara conformidade ou certificação formal com esses
frameworks.

## Avaliação e engenharia

- scikit-learn, métricas:
  https://scikit-learn.org/stable/modules/model_evaluation.html
- GitHub Actions para Python:
  https://docs.github.com/actions/automating-builds-and-tests/building-and-testing-python
- Python Packaging User Guide:
  https://packaging.python.org/en/latest/tutorials/packaging-projects/
- pip-audit:
  https://github.com/pypa/pip-audit

As métricas da V6 são implementadas localmente e testadas por casos conhecidos.
Consulte [EVALUATION.md](EVALUATION.md) para definições, datasets e reprodução.

## Escopo acadêmico futuro

Um estudo representativo deveria:

1. definir população, idiomas e domínios de uso;
2. produzir labels independentes com política de desacordo;
3. separar treino, calibração e teste;
4. comparar TF-IDF, RapidFuzz, embeddings e reranker sob o mesmo dataset;
5. registrar Precision, Recall, F1, métricas de ranking, latência e memória;
6. inspecionar falsos positivos, falsos negativos, parsing e PII residual;
7. avaliar desempenho e erros por grupos relevantes com governança adequada;
8. publicar limitações e artefatos reproduzíveis sem currículos reais.

Os datasets sintéticos atuais são regressões de engenharia e não atendem sozinhos a
esse desenho de pesquisa.
