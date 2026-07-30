from pathlib import Path
from typing import BinaryIO

import pdfplumber


SUPPORTED_TEXT_EXTENSIONS = {".txt", ".md"}


def read_text_from_upload(file_obj: BinaryIO, filename: str) -> str:
    """Read text from an uploaded PDF, TXT, or Markdown file."""
    suffix = Path(filename).suffix.lower()

    if suffix == ".pdf":
        file_obj.seek(0)
        with pdfplumber.open(file_obj) as pdf:
            return "\n".join(page.extract_text() or "" for page in pdf.pages)

    if suffix in SUPPORTED_TEXT_EXTENSIONS:
        file_obj.seek(0)
        content = file_obj.read()
        if isinstance(content, bytes):
            return content.decode("utf-8", errors="replace")
        return str(content)

    raise ValueError(f"Unsupported file type: {suffix or 'unknown'}")
