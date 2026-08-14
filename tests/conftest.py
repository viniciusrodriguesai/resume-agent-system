import os
import sys
from pathlib import Path

os.environ.setdefault("RESUME_ENVIRONMENT", "test")
os.environ.setdefault("RESUME_EMBEDDING_ENABLED", "false")
os.environ.setdefault("RESUME_RERANKER_ENABLED", "false")
os.environ.setdefault("RESUME_DOCLING_ENABLED", "false")
os.environ.setdefault("RESUME_PRESIDIO_ENABLED", "false")
os.environ.setdefault("HF_HUB_OFFLINE", "1")

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
