$ErrorActionPreference = "Stop"
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
uv python install 3.11
uv venv --python 3.11
.\.venv\Scripts\Activate.ps1
uv pip install -r requirements-ai.txt
Write-Host "Ambiente V6.0.5 instalado com uv." -ForegroundColor Green
