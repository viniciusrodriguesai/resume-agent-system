$ErrorActionPreference = "Stop"
python -m ruff check .
python -m pytest --cov=resume_ai --cov-report=term-missing
python -m pip_audit

python -m piplicenses --format=markdown --output-file=THIRD_PARTY_LICENSES.md
