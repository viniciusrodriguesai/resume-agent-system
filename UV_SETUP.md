# Instalação com uv

O projeto inclui `pyproject.toml` e funciona com `uv` no Windows.

```powershell
powershell -ExecutionPolicy Bypass -File scripts\install_uv.ps1
uv run python scripts\preload_models.py --profile demo
uv run streamlit run app.py
```

O arquivo `uv.lock` não foi incluído artificialmente. Gere-o na sua máquina com `uv lock` depois da instalação, pois ele precisa refletir versões realmente resolvidas para Windows e Python 3.11.
