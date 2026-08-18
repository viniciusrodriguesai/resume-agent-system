FROM python:3.11-slim@sha256:9c900dea9e8fb7e16277c179b555cc72d29a352dbc33cff48ad5a0412fd5bfc7
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
WORKDIR /app
RUN useradd --create-home --uid 10001 appuser
COPY requirements.txt .
RUN pip install -r requirements.txt
RUN install -d -o appuser -g appuser /app/data /app/.cache
COPY --chown=appuser:appuser app.py .
COPY --chown=appuser:appuser api ./api
COPY --chown=appuser:appuser assets ./assets
COPY --chown=appuser:appuser examples ./examples
COPY --chown=appuser:appuser resume_ai ./resume_ai
COPY --chown=appuser:appuser .streamlit ./.streamlit
USER appuser
EXPOSE 8501
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8501/_stcore/health')"
CMD ["python", "-m", "streamlit", "run", "app.py", "--server.address=0.0.0.0"]
