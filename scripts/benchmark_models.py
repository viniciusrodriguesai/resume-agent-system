from __future__ import annotations

import argparse
import time

import psutil
from sentence_transformers import SentenceTransformer

MODELS = [
    ("MiniLM ONNX", "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2", "onnx"),
    ("E5-small ONNX", "intfloat/multilingual-e5-small", "onnx"),
]

parser = argparse.ArgumentParser()
parser.add_argument("--runs", type=int, default=3)
args = parser.parse_args()
texts = ["Python, SQL e machine learning em projetos de análise de dados."] * 16

for label, name, backend in MODELS:
    start_load = time.perf_counter()
    try:
        model = SentenceTransformer(name, backend=backend, device="cpu")
    except TypeError:
        model = SentenceTransformer(name, device="cpu")
    load = time.perf_counter() - start_load
    times = []
    for _ in range(args.runs):
        start = time.perf_counter()
        model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
        times.append(time.perf_counter() - start)
    memory = psutil.Process().memory_info().rss / 1024 / 1024
    print(f"{label}: load={load:.2f}s média={sum(times)/len(times):.2f}s RAM={memory:.0f}MB")
