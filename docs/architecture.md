# System Architecture

```text
Resume ───────▶ Resume Agent ────────┐
                                     ├──▶ Matching Agent ─▶ Recommendation Agent ─▶ Review Agent ─▶ Final response
Job description ─▶ Job Agent ────────┘
```

## Responsibilities

- **Resume Agent:** extracts the candidate's skills and main information.
- **Job Agent:** identifies required, desirable, and general skills.
- **Matching Agent:** calculates a weighted compatibility score.
- **Recommendation Agent:** generates practical suggestions.
- **Review Agent:** consolidates the final response and reports warnings.

## Communication model

The project uses a sequential pipeline. Each agent produces a standardized `AgentResult`, which contains its name, summary, structured data, and warnings. The next agent consumes the relevant result instead of reading all raw inputs again.
