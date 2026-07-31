# System Architecture

```text
User
  |
  v
Coordinator Agent
  |
  +--> Resume Agent
  +--> Job Agent
  +--> Experience Agent
  +--> Semantic Matching Agent
  +--> Review Agent
  |       |
  |       +--> revision requested --> Semantic Matching Agent (second pass)
  +--> Recommendation Agent
  +--> Report Agent
  |
  v
Final explainable result
```

Each agent has a specialized responsibility, structured output, confidence,
execution time, and warnings. The Review Agent can request a second matching
pass, creating a feedback loop instead of a fixed one-way pipeline.

The project runs locally and combines a skill ontology, aliases, exact phrase
detection, token overlap, TF-IDF cosine similarity, weighted scoring, evidence
tracing, and deterministic review rules.
