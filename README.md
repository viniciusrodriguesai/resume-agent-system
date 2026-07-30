# Multi-Agent Resume and Job Analysis System

Final project for an Agent-Based Programming course.

## Overview

The system receives a resume and a job description. Five specialized agents cooperate to identify skills, calculate compatibility, detect skill gaps, and generate practical recommendations.

## Agents

1. **Resume Agent:** extracts skills, education, contact information, and experience.
2. **Job Agent:** identifies required, desirable, and general skills.
3. **Matching Agent:** calculates the compatibility score and skill gaps.
4. **Recommendation Agent:** generates practical improvement suggestions.
5. **Review Agent:** consolidates and validates the final response.

## Features

- Paste resume and job-description text directly into the application.
- Upload `.pdf`, `.txt`, or `.md` files.
- View the compatibility percentage.
- See matched and missing skills.
- Receive personalized recommendations.
- Inspect the execution trace of every agent.

## Installation

Create a virtual environment:

```bash
python -m venv .venv
```

Activate it on Windows:

```bash
.venv\Scripts\activate
```

Activate it on Linux or macOS:

```bash
source .venv/bin/activate
```

Install the dependencies:

```bash
pip install -r requirements.txt
```

## Running the application

Start the Streamlit interface:

```bash
streamlit run app.py
```

Run the terminal demonstration:

```bash
python run_demo.py
```

## Input

The system accepts:

- Text pasted manually.
- `.pdf`, `.txt`, or `.md` files.

## Output

The system displays:

- Compatibility percentage and level.
- Required and desirable skills that were matched.
- Required and desirable skills that are missing.
- Practical recommendations.
- The complete execution trace.

## Project structure

```text
resume-analysis-multi-agent-system/
├── app.py
├── pipeline.py
├── run_demo.py
├── requirements.txt
├── agents/
├── utils/
├── examples/
├── docs/
└── slides/
```

## Presentation

The English PowerPoint presentation is included as:

```text
Multi_Agent_Resume_Analysis_Presentation.pptx
```

The editable presentation source is available in the `slides/` directory. To rebuild it:

```bash
cd slides
npm install
npm run build
```

## Matching method

The compatibility score uses weighted categories:

- Required skills: **65%**
- Desirable skills: **25%**
- General skills: **10%**

## Limitations

The current version uses keyword matching. It demonstrates a clear multi-agent architecture, but it does not fully understand context, synonyms, or the quality of a candidate's experience.

## Future improvements

- Semantic comparison with embeddings.
- Integration with large language models.
- Integration with real job platforms.
- Automatic resume rewriting.
- Application-history tracking.
