# Architecture

## Components

### Document Parser

Docling is used when available. The fallback parser supports PDF through
PyPDF, DOCX through python-docx, and plain text formats.

### Privacy and Fairness Agent

Removes direct contact data, personal URLs, the first probable name line, and
selected sensitive fields before matching.

### Resume and Job Structurer Agents

Create structured profiles and link detected skills to a local catalog. The
catalog can be expanded using an imported ESCO CSV.

### Semantic Retriever

Uses a multilingual Sentence Transformer bi-encoder to retrieve the best resume
passages for each requirement. It falls back to local TF-IDF similarity.

### CrossEncoder Reranker

Reranks the top candidates from the first retrieval stage. This avoids applying
the slower pairwise model to every resume passage.

### Explainable Scoring Agent

Uses required, desirable, and neutral weights. Missing required requirements cap
the total score to reduce misleading high scores.

### Review Agent

Looks for borderline missing required requirements. It can route the graph back
to retrieval with a larger candidate set.

### Storage

SQLite stores analysis results locally. No external database is required.

## State

The graph shares a typed state containing the anonymized documents, profiles,
evidence, score, review, recommendations, reports, diagnostics, and execution
trace.
