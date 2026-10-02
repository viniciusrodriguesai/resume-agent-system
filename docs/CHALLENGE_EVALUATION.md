# Expanded end-to-end lexical challenge

The earlier 24-case retrieval-level regression achieved 1.0 accuracy/macro-F1. That small development fixture was not an independent quality benchmark.

A new fixed **36-case** challenge exercises the complete pipeline, including privacy preprocessing, job parsing and evidence decisions. Inputs and labels were written before running this challenge. They cover bilingual enrollment, completed degrees, unrelated subjects, negation, applied experience, cumulative/alternative skills, deployment, and context. All are fictional and internally authored.

Recorded result: **accuracy 0.8333; macro-F1 0.8036**, with all six disagreements published. The source code was not tuned to raise this challenge's reported score. [Cases](../evaluation/challenge/cases-v1.json) · [Complete results](../evaluation/challenge/results-v1.json).

The six disagreements concern enrollment: a completed degree or enrollment in an unrelated subject is expected **missing** under this challenge's strict rubric (both current enrollment and a requested subject are required), while the system assigns **partial** when only one component is present. It does not mark them fully matched. This difference needs independent adjudication: the measured score depends on the rubric's missing/partial boundary and is not a universal accuracy claim.

```bash
python scripts/evaluate_challenge.py --cases evaluation/challenge/cases-v1.json --output challenge-report.json
```

Existing output files cannot be overwritten. The JSON records each decision, evidence, category metrics, dataset/script fingerprints, Python version and source commit. Labels are checked for valid classes and case IDs must be unique. The original run uses source commit `f77a8c5` with the new runner present locally; its exact runner fingerprint is recorded.

## Obtain a genuinely independent evaluation

1. An evaluator who did not develop these rules prepares new fictional/deidentified resume/job pairs and labels, using the [annotation guide](INDEPENDENT_EVALUATION.md).
2. Freeze the evaluation artifact/hash and rubric before selecting models or thresholds. Keep it separate from development cases.
3. Run the unchanged evaluator once, then publish accuracy, macro-F1, class support, category errors and all limitations. Include lexical and optional model settings separately.
4. Do not relabel or tune against these held-out answers to report the same set as independent again.

The included challenge is **not independent**. No external human evaluator, protected new Home Credit labels or quality measurement for optional embeddings/reranker has been obtained. Creating more tests within this project cannot remove that limitation.
