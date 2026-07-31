# Presentation Script

## Problem
Keyword-only resume comparison misses equivalent expressions and does not explain
why a candidate received a score.

## Solution
Specialized agents cooperate to extract resume information, structure job
requirements, locate evidence, calculate scores, review the result, and produce
recommendations and reports.

## Agents
1. Coordinator Agent
2. Resume Agent
3. Job Agent
4. Experience Agent
5. Semantic Matching Agent
6. Review Agent
7. Recommendation Agent
8. Report Agent

## Strongest agent-based feature
The Review Agent may reject the first matching result. The Coordinator Agent then
runs a second pass with adjusted thresholds.

## Explainability
Every requirement receives a priority, category, status, similarity score, and
resume evidence.

## Limitation
The system is deterministic and local. It supports human judgment but must not
replace it.
