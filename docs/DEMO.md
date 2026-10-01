# Try the lexical demo

This demo uses the fictional **Alex Example** resume in `examples/sample_resume.txt` and the Portuguese internship description in `examples/vaga_exemplo.txt`. It does not use a real applicant or require model downloads.

## Run

From the repository root, create a Python 3.11–3.13 environment, install the base requirements, then:

```bash
python -m pip install -r requirements.txt
python run_demo.py
```

The runner explicitly disables embeddings, reranking, and history. It prints a summary followed by a requirement-level Markdown report. For the interface, use `python -m streamlit run app.py` with embeddings and reranking disabled as described in the main README.

## Inspect an actual run

The demo completed on 2026-10-01 with Python 3.12.14 after making optional memory telemetry failure-tolerant. The lexical result reported a heuristic score of 36%, with four matched, two partial, and four missing mandatory requirements. This score is not a calibrated probability or a verified hiring-quality measure.

| Requirement | Observed output | How to interpret it |
| --- | --- | --- |
| Python and SQL | Matched with a Python/SQL project sentence | Inspect the quoted evidence. |
| Pandas, NumPy and scikit-learn | Partial, with a scikit-learn sentence | One tool does not establish all three. |
| University enrollment | Missing; quoted evidence was fragmented | The resume contains enrollment evidence. This is an example of a false negative. |
| Model deployment | Matched to a sentence about building predictive models | The sentence does not establish deployment. This is an example of unsupported matching. |

The mixed-language inputs and privacy preprocessing can affect lexical evidence quality. These observed failures are retained to make the limits inspectable, not hidden behind a high score. No external benchmark or optional embedding/reranker quality is established by this demo.

## Why memory telemetry is optional

In a restricted process environment, `psutil` can raise `NoSuchProcess` or `AccessDenied`. Memory usage is then reported as unknown (`null`), so the completed analysis is still returned. Tests cover these errors, OS access failure, and an available measurement.
