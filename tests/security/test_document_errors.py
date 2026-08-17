import io

import pytest
from pypdf import PdfWriter

from resume_ai.infrastructure.documents import DocumentReader, DocumentReadError
from resume_ai.settings import Settings


def _reader(tmp_path) -> DocumentReader:
    return DocumentReader(
        Settings(
            project_root=tmp_path,
            data_dir=tmp_path / "data",
            cache_dir=tmp_path / "cache",
        )
    )


def test_reader_hides_unexpected_parser_details(tmp_path, monkeypatch) -> None:
    reader = _reader(tmp_path)

    def fail_with_sensitive_message(_upload) -> str:
        raise RuntimeError("private@example.invalid at C:\\private\\resume.pdf")

    monkeypatch.setattr(reader, "_read", fail_with_sensitive_message)

    with pytest.raises(DocumentReadError) as captured:
        reader.read_upload("resume.txt", b"valid UTF-8 text")

    assert str(captured.value) == "Não foi possível processar o documento enviado"
    assert "private" not in str(captured.value)
    assert isinstance(captured.value.__cause__, RuntimeError)


def test_reader_rejects_text_without_extractable_content(tmp_path) -> None:
    reader = _reader(tmp_path)

    with pytest.raises(DocumentReadError, match="extrair texto"):
        reader.read_upload("resume.txt", b" \t\r\n")


def test_reader_rejects_pdf_above_page_limit(tmp_path) -> None:
    writer = PdfWriter()
    for _ in range(41):
        writer.add_blank_page(width=72, height=72)
    content = io.BytesIO()
    writer.write(content)
    reader = _reader(tmp_path)

    with pytest.raises(DocumentReadError, match="mais de 40 páginas"):
        reader.read_upload("resume.pdf", content.getvalue(), "application/pdf")
