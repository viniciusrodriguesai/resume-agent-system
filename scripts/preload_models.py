from __future__ import annotations

import argparse
from typing import Literal

from sentence_transformers import SentenceTransformer

Backend = Literal["torch", "onnx", "openvino"]

MODELS: dict[str, tuple[str, Backend]] = {
    "demo": ("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2", "torch"),
    "balanced": ("intfloat/multilingual-e5-small", "torch"),
    "complete": ("BAAI/bge-m3", "torch"),
}

parser = argparse.ArgumentParser()
parser.add_argument("--profile", choices=MODELS, default="demo")
args = parser.parse_args()
model_name, backend = MODELS[args.profile]
print(f"Carregando {model_name} com backend {backend}...")
try:
    model = SentenceTransformer(model_name, device="cpu", backend=backend)
except TypeError:
    model = SentenceTransformer(model_name, device="cpu")
embedding = model.encode(["Teste do analisador de currículos."], normalize_embeddings=True)
print(f"Modelo pronto. Dimensão: {embedding.shape[-1]}")
