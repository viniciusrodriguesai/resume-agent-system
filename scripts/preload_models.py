from __future__ import annotations

import argparse

from sentence_transformers import SentenceTransformer

MODELS = {
    "demo": ("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2", "onnx"),
    "balanced": ("intfloat/multilingual-e5-small", "onnx"),
    "complete": ("BAAI/bge-m3", "torch"),
}

parser = argparse.ArgumentParser()
parser.add_argument("--profile", choices=MODELS, default="demo")
args = parser.parse_args()
model_name, backend = MODELS[args.profile]
print(f"Carregando {model_name} com backend {backend}...")
kwargs = {"device": "cpu"}
if backend != "torch":
    kwargs["backend"] = backend
try:
    model = SentenceTransformer(model_name, **kwargs)
except TypeError:
    kwargs.pop("backend", None)
    model = SentenceTransformer(model_name, **kwargs)
embedding = model.encode(["Teste do analisador de currículos."], normalize_embeddings=True)
print(f"Modelo pronto. Dimensão: {embedding.shape[-1]}")
