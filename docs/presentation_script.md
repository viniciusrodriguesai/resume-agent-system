# V6 Presentation Script

## 1. Problem

A keyword-only percentage does not explain whether required skills are supported by
specific resume evidence. Synonyms, negations, cumulative requirements, and parsing
errors need an auditable treatment.

## 2. Solution

V6 runs eight sequential agents for privacy, resume structure, job structure,
evidence retrieval, scoring, diagnostic review, recommendations, and reporting. The
runtime is explicit Python orchestration; it has no LangGraph route or iterative
review loop.

## 3. Demonstration

Use only the synthetic repository examples.

1. Select the demo profile and balanced strictness.
2. Load the example or paste synthetic inputs.
3. Confirm the responsible-use notice and run the analysis.
4. Show the overall score and missing required requirements.
5. Inspect one requirement and its ranked evidence.
6. Compare lexical, fuzzy, semantic, reranker, and final scores.
7. Show recommendations, privacy removals, and agent diagnostics.
8. Confirm the backend that actually loaded.
9. Export a Markdown, JSON, or CSV report.

Do not claim an embedding or reranker result when the engine reports fallback.

## 4. Architecture

Streamlit and FastAPI call the same `ResumeAnalysisService`. Domain rules, agents,
infrastructure, and presentation are separated. SQLite is the default implementation
of an application history port. The review agent reports threshold and required-skill
concerns; it does not change the score or trigger another retrieval pass.

## 5. Evaluation

Run retrieval and full-pipeline benchmarks on synthetic versioned datasets. Explain
Precision, Recall, F1, Precision@K, Recall@K, MRR, NDCG@K, mean and p95 latency, and
RSS delta. Preserve dataset hash, parameters, environment, and backend status instead
of copying results from another machine.

## 6. Engineering evidence

Show typed `AgentResult` diagnostics, JSON logs, request correlation, hardened file
validation, safe API errors, test-suite separation, the Python 3.11 to 3.13 CI matrix,
Python distributions, and the non-root container design.

## 7. Limitations

Anonymization and matching can fail, complex layouts may parse incorrectly, the
current datasets are small and synthetic, systematic bias evaluation is unfinished,
and process-local controls do not replace production infrastructure. The tool
supports human review and never makes the hiring decision.
