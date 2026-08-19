# Theoretical Project Report — V6

## Topic

A local, explainable multi-agent system for comparing resume evidence with job
requirements.

## Problem

Job descriptions mix mandatory requirements, preferences, and responsibilities.
Resume wording often differs from the job wording, and a mention does not necessarily
demonstrate experience. A single opaque percentage hides missing mandatory evidence,
document parsing errors, and uncertainty.

## Objective

Build a system that decomposes matching into testable responsibilities, preserves the
evidence behind each status, minimizes personal data, measures model and pipeline
quality, and supports rather than replaces human judgment.

## Agent concept

In this project, an agent is a bounded software component with one responsibility and
a typed output. It is not assumed to be an autonomous language model. Each stage
returns its domain value plus an `AgentResult` containing status, duration,
confidence, warnings, evidence references, and operational metadata.

The agents execute sequentially under `ResumeAnalysisService`:

1. **Privacy Agent** removes direct identifiers before embedding.
2. **Resume Agent** structures skills, education, experience, projects, and chunks.
3. **Job Agent** extracts title, responsibilities, and prioritized requirements.
4. **Evidence Agent** retrieves and optionally reranks resume passages.
5. **Scoring Agent** classifies evidence and calculates weighted compatibility.
6. **Review Agent** flags mandatory gaps and borderline thresholds.
7. **Recommendation Agent** proposes honest, prioritized actions.
8. **Report Agent** prepares an explainable report.

The Review Agent is diagnostic. It does not modify the score or route the pipeline
back to retrieval. V6 does not use LangGraph orchestration.

## Layered architecture

Streamlit and FastAPI are input and output adapters. The application service composes
agents and infrastructure. Domain models and scoring do not depend on either UI
framework. Infrastructure provides document parsing, privacy, retrieval, cache,
telemetry, and SQLite history.

The application depends on an `AnalysisHistoryWriter` port. This keeps the use case
independent from the default SQLite implementation and allows disabled or alternative
storage without changing the pipeline.

## Evidence retrieval

For each requirement, V6 ranks bounded anonymized resume chunks with:

- TF-IDF similarity;
- RapidFuzz approximate similarity;
- local concept and alias coverage;
- optional Sentence Transformer similarity;
- optional CrossEncoder reranking.

With embeddings, initial retrieval uses a weighted combination of semantic, lexical,
fuzzy, and concept scores. Without embeddings, the weights are redistributed across
lexical, fuzzy, and concept coverage. Exact phrases and complete concept coverage
receive bounded boosts. Explicit negation lowers evidence, and incomplete cumulative
requirements cannot become complete only through reranking.

The fallback is a first-class mode, not an unreported failure. Backend status and
agent warnings distinguish configured models from models actually loaded.

## Compatibility scoring

Evidence is classified according to strictness:

| Strictness | Matched | Partial |
|---|---:|---:|
| Flexible | at least 0.50 | at least 0.28 |
| Balanced | at least 0.60 | at least 0.35 |
| Conservative | at least 0.70 | at least 0.43 |

Statuses contribute:

- matched: 1.00;
- partial: 0.55;
- missing: 0.00.

Requirement priorities weight those values:

- required: 1.00;
- desired: 0.45;
- neutral: 0.20.

The normalized score is:

```text
overall = 100 × sum(priority_weight × status_value)
                / sum(priority_weight)
```

If at least half of required requirements are missing, the score is capped at 55. If
at least one quarter are missing, it is capped at 72. This prevents numerous
preferences from hiding substantial mandatory gaps.

The score measures textual support under configured rules. It does not establish
professional competence, future performance, or hiring suitability.

## Privacy and security

Resume anonymization happens before structuring and embeddings. Regex-based
recognizers are always available; Presidio is optional. Upload validation checks
filenames, declared and detected format, archive structure, compression, XML, text
encoding, size, and parser-specific limits.

Automatic anonymization and parsing remain fallible. Results, including anonymized
evidence, should still be treated as sensitive. The default history stores a limited
summary, not source documents or evidence.

## Evaluation

Versioned synthetic datasets support:

- classification Precision, Recall, and F1;
- Precision@K, Recall@K, MRR, and NDCG@K;
- mean and p95 latency;
- estimated RSS increase;
- per-agent duration in the full pipeline.

Benchmarks disable result cache and history, record dataset hash and environment, and
fail on nondeterministic rankings or labels. These datasets are engineering
regressions, not evidence of population validity or fairness.

## Advantages

- separates responsibilities and test boundaries;
- keeps evidence visible;
- records fallback and uncertainty;
- supports CPU-only local execution;
- minimizes external data transfer;
- shares one use case across UI and API;
- permits replaceable persistence;
- provides reproducible evaluation artifacts.

## Limitations

- extraction can fail on image PDFs and complex layouts;
- anonymization can miss direct or indirect identifiers;
- lexical methods favor similar wording;
- embedding and reranker models can reproduce training bias;
- the local catalog has limited domain coverage;
- thresholds are manually configured rather than calibrated;
- current datasets are small and synthetic;
- systematic bias evaluation is unfinished;
- SQLite, metrics, and rate limiting are process-local;
- parsers are not isolated in a sandbox.

## Responsible use and future work

The system should remain assistive, contestable, and subject to human review. It
must not infer sensitive traits, automatically reject candidates, or produce a final
ranking of people.

Appropriate future research includes larger reviewed datasets, threshold calibration,
bias evaluation, improved multi-column extraction and OCR, model provenance, SBOM,
and parser isolation. Distributed queues, mandatory PostgreSQL, and a React rewrite
are engineering options, not requirements of this version.
