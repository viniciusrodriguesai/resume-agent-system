$ErrorActionPreference = "Stop"
$env:RESUME_PROFILE="demo"
$env:RESUME_EMBEDDING_MODEL="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
$env:RESUME_EMBEDDING_BACKEND="torch"
$env:RESUME_RERANKER_ENABLED="false"
$env:RESUME_DOCLING_ENABLED="false"
$env:RESUME_PRESIDIO_ENABLED="false"
$env:TOKENIZERS_PARALLELISM="false"
python -m streamlit run app.py
