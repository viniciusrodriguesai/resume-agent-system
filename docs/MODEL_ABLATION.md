# Optional-model ablation on the internal challenge

The same 36 fictional cases and unchanged matching pipeline were evaluated under three modes. Only embedding/reranker flags differ; E5-small and multilingual mMARCO MiniLM are fixed choices, not selected using these results. CPU inference uses two Torch threads and seed 0. The runner explicitly fails if a requested model cannot load or inference falls back to lexical. Models actually loaded and returned no backend errors.

| Mode | Accuracy | Macro-F1 | Median case ms | p95 case ms | Process high-water MiB |
| --- | --- | --- | --- | --- | --- |
| lexical | 0.8333 | 0.8036 | 7.90 | 10.10 | 240.3 |
| embedding | 0.8333 | 0.8036 | 52.65 | 67.27 | 917.7 |
| reranked | 0.8333 | 0.8036 | 84.64 | 116.45 | 1292.3 |

All 36 predicted labels are identical across modes, including the six enrollment missing/partial rubric disagreements. Semantic/reranking scores can change without changing the final policy-constrained labels. This challenge provides no evidence of an accuracy benefit from these optional models, and they increase measured latency. Prefer the lexical demo for this bounded demonstration; do not infer that optional models never help on larger retrieval pools or paraphrased requirements.

This remains internal developer-authored evaluation. The same cases were already inspected during lexical evaluation; these are not fresh protected labels. It does not resolve independent evaluation. Two annotators and adjudication remain necessary before a generalization claim. No matcher or threshold was tuned to these results.

## Reproduction and provenance

Use Linux/WSL with Python 3.12 and the tracked environment lock `requirements-model-evaluation.txt`. The environment used Torch 2.8.0+cpu, sentence-transformers 5.1.2 and transformers 4.57.6. Install CPU Torch from its official wheel index, then the lock with that index available:

```bash
python -m pip install --extra-index-url https://download.pytorch.org/whl/cpu -r requirements-model-evaluation.txt
python scripts/evaluate_models.py --cases evaluation/challenge/cases-v1.json --mode lexical --output lexical-new.json
python scripts/evaluate_models.py --cases evaluation/challenge/cases-v1.json --mode embedding --output embedding-new.json
python scripts/evaluate_models.py --cases evaluation/challenge/cases-v1.json --mode reranked --output reranked-new.json
```

Model repositories: `intfloat/multilingual-e5-small` and `cross-encoder/mmarco-mMiniLMv2-L12-H384-v1`. Snapshot commit revisions are recorded in each model report. The application loader uses the repository default revision, so future downloads may differ: compare the recorded revision before calling a rerun an exact model reproduction. The lock fixes packages, not model repository revisions. No model weights are committed.

All per-case outcomes/evidence, settings, source/dataset hashes, revisions and package versions are under `evaluation/challenge/models-v1/`. The runner was added after source commit `844ce74f75aac7f1b31481749eab2cbe7388e9e9`; its exact new contents are identified by script SHA-256. An earlier unpublished timing run was repeated after formatting the runner so these reports match the final script hash.

Timing is one serial developer-run pass per mode in an ephemeral Linux environment, with pretrained weights already cached and lazy chunk-cache reuse within each pass. Cold model load time is reported separately and can include downloads. Per-case p95 is a small-sample descriptive order statistic. RSS is process high-water usage (including Python/Torch), not model weight size or measured Render memory. These are not production throughput or cold-start service benchmarks.
