from sentence_transformers import CrossEncoder, SentenceTransformer

MODELO_EMBEDDINGS='BAAI/bge-m3'
MODELO_RERANKER='BAAI/bge-reranker-v2-m3'

print('Baixando o modelo de embeddings...')
SentenceTransformer(MODELO_EMBEDDINGS)
print('Baixando o reranker...')
CrossEncoder(MODELO_RERANKER)
print('Modelos armazenados no cache local do Hugging Face.')
