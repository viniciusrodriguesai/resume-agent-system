# Professional Multi-Agent Resume AI

A local, multilingual, explainable system for comparing resumes with job
descriptions. The application combines a real conditional agent graph,
document parsing, privacy preprocessing, a local skill catalog, semantic
retrieval, CrossEncoder reranking, evidence-based scoring, self-review,
recommendations, reports, history, evaluation, tests, and GitHub Actions.

## What makes this version stronger

- **LangGraph workflow:** agents run through a conditional graph, and the Review
  Agent can send borderline cases back to the retrieval stage.
- **Sentence Transformers:** a multilingual bi-encoder retrieves semantically
  related resume evidence.
- **CrossEncoder reranking:** the strongest retrieved passages are reranked for
  better pairwise relevance.
- **Docling support:** PDF and DOCX documents can be converted into structured
  Markdown when Docling is installed.
- **Automatic fallbacks:** the app still works without heavy AI packages by
  using local lexical TF-IDF similarity, PyPDF, and python-docx.
- **Privacy and fairness:** direct identifiers and selected sensitive lines are
  removed before matching.
- **Explainability:** every requirement shows its best resume evidence, score,
  priority, status, and matching engine.
- **SQLite history:** analyses are saved locally.
- **ESCO-ready catalog:** the project includes a sample skill catalog and a
  script for importing an official ESCO CSV into SQLite.
- **Evaluation:** labeled examples can be evaluated with accuracy, precision,
  recall, and F1.
- **Continuous integration:** GitHub Actions runs tests on every push and pull
  request.

## Agent graph

```text
START
  ↓
Privacy and Fairness Agent
  ↓
Resume Structurer Agent
  ↓
Job Structurer Agent
  ↓
Semantic Retriever + CrossEncoder Reranker
  ↓
Explainable Scoring Agent
  ↓
Review Agent ── revise ──┐
  │                       │
  └── approve             └── back to retrieval
          ↓
Recommendation Agent
          ↓
Report Agent
          ↓
END
```

## Fast setup in VS Code

Open this project folder in VS Code and run:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

The basic version opens at:

```text
http://localhost:8501
```

It works immediately with the lexical fallback.

On Windows, you can also double-click:

```text
run.bat
```

## Install the complete local AI version

The complete setup is larger because it installs document and transformer
models:

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-full.txt
python scripts\download_models.py
python -m streamlit run app.py
```

Or double-click:

```text
install_full_ai.bat
```

The first model download requires internet access. After the models are cached,
analysis runs locally without an API key.

If a heavy dependency does not install on your current Python version, create
the environment with Python 3.11 or 3.12:

```powershell
py -3.12 -m venv .venv
```

## Application modes

### Full local AI

Uses:

- `paraphrase-multilingual-MiniLM-L12-v2`
- `mmarco-mMiniLMv2-L12-H384-v1`
- LangGraph
- Docling

### Automatic fallback

Uses:

- local skill aliases;
- TF-IDF cosine similarity;
- exact phrase matching;
- PyPDF;
- python-docx;
- the same scoring, review, reporting, history, and UI.

## Import a complete ESCO skills file

Download an ESCO skills CSV from the official ESCO download page. Then run:

```powershell
python scripts\import_esco.py "C:\path	o\esco_skills.csv"
```

The script recognizes common label, alternative-label, and concept-URI column
names and creates:

```text
data/esco.sqlite
```

Restart the app after importing.

## Run the demonstration

```powershell
python run_demo.py
```

## Run tests

```powershell
pytest -q
```

or:

```text
run_tests.bat
```

## Evaluate matching quality

The included example dataset uses the labels `matched`, `partial`, and
`missing`.

Fallback evaluation:

```powershell
python scripts\evaluate.py
```

Full-model evaluation:

```powershell
python scripts\evaluate.py --full-ai
```

Replace `examples/evaluation_labels.csv` with a larger manually labeled dataset
for a valid academic experiment.

## Project structure

```text
resume-agent-system/
├── app.py
├── resume_ai/
│   ├── analyzer.py
│   ├── catalog.py
│   ├── config.py
│   ├── documents.py
│   ├── evaluation.py
│   ├── privacy.py
│   ├── profiles.py
│   ├── reporting.py
│   ├── scoring.py
│   ├── semantic.py
│   ├── state.py
│   ├── storage.py
│   └── text.py
├── data/
│   └── esco_sample_skills.csv
├── examples/
│   ├── sample_resume.txt
│   ├── sample_job.txt
│   └── evaluation_labels.csv
├── scripts/
│   ├── download_models.py
│   ├── evaluate.py
│   └── import_esco.py
├── tests/
├── docs/
└── .github/workflows/tests.yml
```

## Responsible-use limitation

This application is decision support, not an automatic hiring system. A human
must review the evidence, candidate context, accessibility needs, possible
biases, and the limitations of the models. The application must not be the sole
basis for accepting or rejecting a candidate.

## License

MIT
