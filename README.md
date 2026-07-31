# Advanced Multi-Agent Resume and Job Analysis System

A fully local multi-agent system that compares a resume with a job description,
extracts evidence, calculates explainable compatibility scores, reviews its own
analysis, and generates prioritized recommendations and downloadable reports.

## Main features

- Coordinator Agent controlling the complete workflow
- Resume and job structure extraction
- Local hybrid semantic matching
- Evidence for every requirement
- Required, desirable, and neutral priorities
- Compatibility scores by category
- Review Agent with a second-pass feedback loop
- Prioritized recommendations
- Agent confidence, timing, warnings, and execution trace
- Markdown and JSON report downloads
- No paid API and no API key

## Run in VS Code on Windows

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Then open:

```text
http://localhost:8501
```

You may also double-click `install_and_run.bat`.

## Run the demonstration

```powershell
python run_demo.py
```

## Run the tests

```powershell
python -m pytest -q
```

## Project structure

```text
resume-agent-system/
├── agents/
├── services/
├── utils/
├── tests/
├── examples/
├── docs/
├── app.py
├── pipeline.py
├── run_demo.py
└── requirements.txt
```

## Local AI method

The matching engine combines canonical skill aliases, exact phrase matching,
token overlap, local TF-IDF cosine similarity, weighted scoring, evidence
extraction, and a review loop.

## Ethical limitation

This system must support, not replace, human evaluation. Recommendations must not
invent skills or experience.
