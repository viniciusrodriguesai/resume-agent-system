from __future__ import annotations
import io
from typing import Any
from pypdf import PdfReader

def read_text_from_upload(uploaded_file: Any, file_name: str) -> str:
    suffix = file_name.lower().rsplit(".", 1)[-1]
    if suffix in {"txt", "md"}:
        return uploaded_file.getvalue().decode("utf-8", errors="replace")
    if suffix == "pdf":
        reader = PdfReader(io.BytesIO(uploaded_file.getvalue()))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    raise ValueError("Unsupported file format.")
