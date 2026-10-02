# Resume Match AI

A local application that compares a resume with a job description and returns evidence for individual requirements, a compatibility score and review suggestions. Built with Python, Streamlit and FastAPI, with optional embedding retrieval and reranking.

[Português](README.pt-BR.md) · [Architecture](docs/architecture.md) · [API](docs/API.md) · [Validation](VALIDATION.md)

[Try the runnable lexical demo](docs/DEMO.md), including an actual output walkthrough and observed matching failures.

## What it demonstrates

- Separate parsing, requirement extraction, retrieval, scoring and review stages.
- A deterministic lexical path that works without downloading models.
- Optional multilingual embedding models and reranking, loaded lazily.
- A Streamlit interface and typed FastAPI endpoints.
- Requirement-level evidence, diagnostics and Markdown/JSON/CSV exports.
- Privacy controls, input limits, tests and CI across Python 3.11–3.13.

Here, “agents” means coordinated application stages. Model availability and execution status are reported explicitly; enabling a profile does not prove that its optional model loaded.

## Quick start

Create and activate a Python 3.11–3.13 virtual environment, then:

```bash
python -m pip install -r requirements.txt
```

For the lexical mode, set these environment variables (or use a local `.env`):

```dotenv
RESUME_EMBEDDING_ENABLED=false
RESUME_RERANKER_ENABLED=false
```

Start the interface:

```bash
python -m streamlit run app.py
```

Or start the API:

```bash
python -m uvicorn api.main:app --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000/docs` for the API contract. Optional model dependencies are in `requirements-ai.txt`; additional parsing/privacy integrations are in `requirements-full.txt`. See [configuration](docs/CONFIGURATION.md) and [deployment](docs/DEPLOYMENT.md).

## Quality checks

```bash
python -m pip install -r requirements-dev.txt
python -m pytest
python -m ruff check .
python -m mypy .
```

NumPy is bounded below 2.3 to keep its typing interface compatible with this project's Python 3.11 type-checking target. NumPy 2.2.4 was used for the verified local checks; dependency ranges are not a full environment lock.

## Evaluation limits

The bundled evaluation cases are small and synthetic. They are useful for regression checks, not evidence of hiring accuracy, fair treatment or generalization to real applicants. Scores and agent confidence values are heuristics, not calibrated probabilities. Optional model quality, real-world bias and threshold calibration still require evaluation.

## Privacy and responsible use

Use synthetic resumes for public examples. Local processing does not guarantee complete anonymization: regex/optional Presidio can miss identifying details, complex PDFs can parse incorrectly, and file parsing is not an isolated malware sandbox. Review storage configuration before using real resumes.

The tool supports human review and resume improvement. It must not make automatic hiring decisions, infer sensitive attributes or invent experience.

## Status and documentation

There is no official public deployment. Docker, large optional models and every runtime profile were not validated during the portfolio audit. [VALIDATION.md](VALIDATION.md) records the tested configuration and distinguishes current evidence from historical V5.2 results.

- [Security](SECURITY.md) and [authentication](AUTHENTICATION.md).
- [Evaluation methodology](docs/EVALUATION.md).
- [Observability](docs/OBSERVABILITY.md).
- [Portuguese detailed overview](README.pt-BR.md).

## Author and license

Academic project by Vinicius Rodrigues (Vinicius Mangueira). [MIT](LICENSE).

## Expanded evaluation and hosting

Inspect the [36-case end-to-end challenge](docs/CHALLENGE_EVALUATION.md), including six missing/partial disagreements, and the [independent annotation handoff](docs/INDEPENDENT_EVALUATION.md). This remains internal evidence. The [Render guide](docs/HOSTED_DEMO.md) prepares the actual lexical Streamlit app for a free instance; a live URL is not claimed until verified.
