# Theoretical Project Report

## Topic

A multi-agent system for analyzing compatibility between a resume and a job description.

## Problem

Candidates often struggle to determine whether their resume is aligned with a position. Job descriptions may mix mandatory requirements, preferred qualifications, and implicit skills. This project proposes an agent-based solution that decomposes the analysis into smaller and more explainable tasks.

## Objective

Build a simple system in which multiple agents cooperate to analyze a resume and a job description, calculate compatibility, and generate practical recommendations.

## Agent concept

An agent is a software entity that receives information from its environment, processes it, and performs an action or produces a response. In this project, every agent has a specific responsibility and communicates through structured results.

## Agents used

### 1. Resume Agent

Extracts skills, contact information, education, and relevant experience from the resume.

### 2. Job Agent

Analyzes the job description and separates required, desirable, and general skills.

### 3. Matching Agent

Compares resume skills with job requirements and calculates compatibility.

### 4. Recommendation Agent

Generates suggestions for improving the resume or learning missing skills.

### 5. Review Agent

Consolidates the final response and checks warnings produced by previous agents.

## Architecture

The system uses a sequential architecture. The output of one agent becomes input for the next agent. This design makes the process easier to explain, test, and demonstrate.

Main flow:

1. Receive the resume and job description.
2. Extract skills and relevant information from the resume.
3. Extract and classify skills from the job description.
4. Compare the candidate profile with the position.
5. Generate recommendations.
6. Review and present the final response.

## Compatibility criterion

The score uses different weights:

- Required skills: **65%** of the score.
- Desirable skills: **25%** of the score.
- General skills: **10%** of the score.

Required skills receive the greatest weight because they normally have the strongest influence on candidate eligibility.

The formula is:

```text
score = 100 × (0.65 × required_match
             + 0.25 × desirable_match
             + 0.10 × general_match)
```

Each match value is the proportion of requested skills found in the resume for that category.

## Advantages

- Divides a complex problem into smaller responsibilities.
- Makes every processing stage visible.
- Produces an explainable result instead of only a numerical score.
- Allows each agent to be improved independently.
- Can later integrate semantic models or real job platforms.

## Limitations

- Keyword matching may not understand complex synonyms or context.
- The result depends on the clarity and completeness of both texts.
- The score measures textual skill overlap, not real professional proficiency.
- The current version does not replace human evaluation.

## Future improvements

- Use embeddings for semantic comparison.
- Integrate a large language model for contextual extraction.
- Connect the system to LinkedIn, Wellfound, or other job platforms.
- Automatically generate a tailored resume version.
- Store application history and candidate progress.
